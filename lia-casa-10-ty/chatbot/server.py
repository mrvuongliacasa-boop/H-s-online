#!/usr/bin/env python3
"""Máy chủ chatbot Lia Casa: nhận tin nhắn Facebook Messenger / Instagram DM / Zalo OA và trả lời tự động.

Chạy:   cd lia-casa-10-ty && python3 -m chatbot.server        (cổng mặc định 8080, đặt PORT để đổi)
Webhook:
  Facebook/Instagram : https://<tên-miền>/webhook/facebook   (GET xác minh + POST tin nhắn)
  Zalo OA            : https://<tên-miền>/webhook/zalo
  Kiểm tra sống      : https://<tên-miền>/health

Biến môi trường (KHÔNG ghi vào code / repo):
  FB_VERIFY_TOKEN   chuỗi tự đặt, nhập giống hệt ở Meta App > Webhooks
  FB_APP_SECRET     App Secret – để xác thực chữ ký X-Hub-Signature-256
  FB_PAGE_TOKEN     Page Access Token (quyền pages_messaging; IG cần thêm instagram_manage_messages)
  ZALO_APP_ID, ZALO_APP_SECRET, ZALO_OA_SECRET   thông tin ứng dụng Zalo
  ZALO_ACCESS_TOKEN, ZALO_REFRESH_TOKEN          token OA (tự làm mới khi hết hạn)
  LEAD_WEBHOOK      (tuỳ chọn) URL Google Apps Script nhận lead – dùng chung với landing page
  NOTIFY_WEBHOOK    (tuỳ chọn) URL nhận thông báo lead nóng (Zapier/Make -> nhóm Zalo sale)
Lead luôn được ghi vào chatbot/data/leads.csv (đã .gitignore).
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import json
import logging
import os
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from chatbot.engine import Bot, Reply, as_plain_text

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
STATE_FILE, LEADS_FILE, ZALO_TOKEN_FILE = DATA / "state.json", DATA / "leads.csv", DATA / "zalo-token.json"
GRAPH = "https://graph.facebook.com/v21.0"
ENV = os.environ.get
log = logging.getLogger("liacasa-bot")
lock = threading.Lock()
bot = Bot()


# ---------------- trạng thái hội thoại & lead ----------------
def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


STATE = load_state()


def save_state() -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(STATE, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def record_lead(channel: str, user_id: str, name: str, lead: dict) -> None:
    row = {"thoi_gian": datetime.now().isoformat(timespec="seconds"), "kenh": channel, "user_id": user_id,
           "ten": name, **lead}
    cols = ["thoi_gian", "kenh", "user_id", "ten", "sdt", "tag", "nhu_cau", "sku", "ngan_sach", "dien_tich", "lich_hen"]
    new = not LEADS_FILE.exists()
    with LEADS_FILE.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)
    payload = {"ho_ten": name, "sdt": lead.get("sdt"), "san_pham": lead.get("sku"), "ngan_sach": lead.get("ngan_sach", ""),
               "ghi_chu": f"[chatbot {channel}] {lead.get('nhu_cau', '')} {lead.get('dien_tich', '')} {lead.get('lich_hen', '')}".strip(),
               "nguon": channel, "utm": {}, "thoi_gian": row["thoi_gian"]}
    for url in filter(None, [ENV("LEAD_WEBHOOK"), ENV("NOTIFY_WEBHOOK") if lead.get("tag") == "nong" else None]):
        try:
            requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode(), timeout=10,
                          headers={"Content-Type": "text/plain; charset=utf-8"})
        except requests.RequestException as e:
            log.warning("Gửi lead tới webhook lỗi: %s", e)
    log.info("LEAD %s %s %s", channel, lead.get("tag"), lead.get("sku"))


def converse(channel: str, user_id: str, text: str, payload: str | None, name: str = "") -> list[Reply]:
    key = f"{channel}:{user_id}"
    with lock:
        st = STATE.setdefault(key, {})
        replies = bot.handle(text, st, payload=payload, name=name)
        lead = st.pop("lead", None)
        if st.get("handoff") and not st.get("handoff_notified"):
            st["handoff_notified"] = True
            lead = lead or {"sdt": "", "tag": "nong", "nhu_cau": "can_nguoi_that", "sku": st.get("sku", "")}
        save_state()
    if lead:
        record_lead(channel, user_id, name, lead)
    return replies


# ---------------- Facebook Messenger / Instagram ----------------
def fb_signature_ok(body: bytes, header: str | None) -> bool:
    secret = ENV("FB_APP_SECRET")
    if not secret:
        log.warning("Chưa đặt FB_APP_SECRET – bỏ qua xác thực chữ ký (chỉ dùng khi thử nghiệm)")
        return True
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return bool(header) and hmac.compare_digest(expected, header)


def fb_send(recipient: str, r: Reply, instagram: bool) -> None:
    token = ENV("FB_PAGE_TOKEN")
    if not token:
        log.error("Chưa đặt FB_PAGE_TOKEN"); return
    msg: dict = {"text": r.text[:2000]}
    if r.options:
        msg["quick_replies"] = [{"content_type": "text", "title": label[:20], "payload": pl} for label, pl in r.options[:13]]
    body = {"recipient": {"id": recipient}, "messaging_type": "RESPONSE", "message": msg}
    url = f"{GRAPH}/me/messages"
    resp = requests.post(url, params={"access_token": token}, json=body, timeout=15)
    if resp.status_code != 200:
        log.error("Gửi tin %s lỗi %s: %s", "IG" if instagram else "FB", resp.status_code, resp.text[:300])


def handle_facebook(data: dict) -> None:
    instagram = data.get("object") == "instagram"
    channel = "instagram" if instagram else "facebook"
    for entry in data.get("entry", []):
        for ev in entry.get("messaging", []):
            msg, sender = ev.get("message", {}), ev.get("sender", {}).get("id")
            if not sender or msg.get("is_echo"):
                continue
            # nhân viên trả lời từ Inbox -> echo; Page có thể bật lại bot bằng nhãn/thao tác riêng
            payload = (msg.get("quick_reply") or {}).get("payload") or (ev.get("postback") or {}).get("payload")
            text = msg.get("text", "") or (ev.get("postback") or {}).get("title", "")
            if not text and not payload:
                continue  # ảnh/sticker: để nhân viên xử lý
            for r in converse(channel, sender, text, payload):
                fb_send(sender, r, instagram)


# ---------------- Zalo OA ----------------
def zalo_token() -> str | None:
    try:
        saved = json.loads(ZALO_TOKEN_FILE.read_text(encoding="utf-8"))
        return saved.get("access_token")
    except (FileNotFoundError, json.JSONDecodeError):
        return ENV("ZALO_ACCESS_TOKEN")


def zalo_refresh() -> str | None:
    try:
        saved = json.loads(ZALO_TOKEN_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        saved = {}
    refresh = saved.get("refresh_token") or ENV("ZALO_REFRESH_TOKEN")
    if not (refresh and ENV("ZALO_APP_ID") and ENV("ZALO_APP_SECRET")):
        log.error("Thiếu ZALO_REFRESH_TOKEN / ZALO_APP_ID / ZALO_APP_SECRET để làm mới token"); return None
    resp = requests.post("https://oauth.zaloapp.com/v4/oa/access_token", timeout=15,
                         headers={"secret_key": ENV("ZALO_APP_SECRET")},
                         data={"refresh_token": refresh, "app_id": ENV("ZALO_APP_ID"), "grant_type": "refresh_token"})
    tok = resp.json() if resp.ok else {}
    if "access_token" not in tok:
        log.error("Làm mới token Zalo lỗi: %s", resp.text[:300]); return None
    ZALO_TOKEN_FILE.write_text(json.dumps(tok), encoding="utf-8")
    return tok["access_token"]


def zalo_send(user_id: str, r: Reply) -> None:
    body = {"recipient": {"user_id": user_id}, "message": {"text": as_plain_text(r)[:2000]}}
    for attempt in range(2):
        token = zalo_token() if attempt == 0 else zalo_refresh()
        if not token:
            return
        resp = requests.post("https://openapi.zalo.me/v3.0/oa/message/cs", json=body, timeout=15,
                             headers={"access_token": token})
        res = resp.json() if resp.ok else {"error": resp.status_code}
        if res.get("error") in (0, None):
            return
        if res.get("error") not in (-216, -124):  # -216/-124: token hết hạn/không hợp lệ -> làm mới rồi thử lại
            log.error("Gửi tin Zalo lỗi: %s", res); return


def zalo_signature_ok(raw: bytes, data: dict, header: str | None) -> bool:
    oa_secret = ENV("ZALO_OA_SECRET")
    if not oa_secret:
        log.warning("Chưa đặt ZALO_OA_SECRET – bỏ qua xác thực chữ ký (chỉ dùng khi thử nghiệm)")
        return True
    base = f"{data.get('app_id', '')}{raw.decode('utf-8')}{data.get('timestamp', '')}{oa_secret}"
    expected = "mac=" + hashlib.sha256(base.encode()).hexdigest()
    return bool(header) and hmac.compare_digest(expected, header)


def handle_zalo(data: dict) -> None:
    if data.get("event_name") != "user_send_text":
        return
    uid = data.get("sender", {}).get("id")
    text = data.get("message", {}).get("text", "")
    if uid:
        for r in converse("zalo", uid, text, None):
            zalo_send(uid, r)


# ---------------- HTTP ----------------
class Handler(BaseHTTPRequestHandler):
    def _reply(self, code: int, body: str = "OK") -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        if url.path == "/health":
            return self._reply(200, "ok")
        if url.path == "/webhook/facebook":
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == ENV("FB_VERIFY_TOKEN") and ENV("FB_VERIFY_TOKEN"):
                return self._reply(200, q.get("hub.challenge", ""))
            return self._reply(403, "forbidden")
        if url.path == "/webhook/zalo":
            return self._reply(200, "ok")
        self._reply(404, "not found")

    def do_POST(self):  # noqa: N802
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._reply(400, "bad json")
        path = urlparse(self.path).path
        if path == "/webhook/facebook":
            if not fb_signature_ok(raw, self.headers.get("X-Hub-Signature-256")):
                return self._reply(403, "bad signature")
            self._reply(200)  # trả 200 ngay để Meta không gửi lại
            threading.Thread(target=self._safe, args=(handle_facebook, data), daemon=True).start()
        elif path == "/webhook/zalo":
            if not zalo_signature_ok(raw, data, self.headers.get("X-ZEvent-Signature")):
                return self._reply(403, "bad signature")
            self._reply(200)
            threading.Thread(target=self._safe, args=(handle_zalo, data), daemon=True).start()
        else:
            self._reply(404, "not found")

    @staticmethod
    def _safe(fn, data):
        try:
            fn(data)
        except Exception:  # không để 1 tin lỗi làm sập máy chủ
            log.exception("Lỗi xử lý webhook")

    def log_message(self, fmt, *args):
        log.debug(fmt, *args)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    port = int(ENV("PORT", "8080"))
    log.info("Chatbot Lia Casa chạy tại cổng %s", port)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
