#!/usr/bin/env python3
"""Tự đăng video lên Fanpage và tự tạo quảng cáo "Nhắn tin" (Facebook + Instagram) – Meta Graph/Marketing API.

Quy trình:  make_videos.py  ->  dang_bai_ads.py dang  ->  dang_bai_ads.py ads  ->  dang_bai_ads.py toi-uu (hằng ngày)

  python3 tools/dang_bai_ads.py dang   [--lich "2026-11-12 11:30,2026-11-12 20:00,..."] [--that]
        Đăng từng video trong video/out/danh-sach-dang.json lên Page (kèm caption).
        --lich: hẹn giờ đăng (giờ VN), mỗi video 1 mốc; không có -> đăng ngay.
  python3 tools/dang_bai_ads.py ads    --ngan-sach 200000 [--bat] [--that]
        Tạo 1 chiến dịch Tương tác/Nhắn tin, mỗi video 1 nhóm QC (ngân sách/ngày VND) + 1 quảng cáo nút "Gửi tin nhắn".
        Mặc định tạo ở trạng thái TẠM DỪNG để bạn duyệt; thêm --bat để chạy luôn.
  python3 tools/dang_bai_ads.py toi-uu [--cpl-toi-da 250000] [--chi-toi-thieu 300000] [--that]
        Đọc kết quả 3 ngày: quảng cáo đã chi >= chi-toi-thieu mà chi phí/tin nhắn > cpl-toi-da (hoặc 0 tin nhắn) -> tạm dừng.

Không có --that: CHẠY THỬ, chỉ in ra những gì sẽ làm (không gọi API ghi).

Biến môi trường (KHÔNG commit):
  META_PAGE_ID, META_PAGE_TOKEN        Page + Page Access Token (pages_manage_posts, pages_read_engagement)
  META_AD_ACCOUNT_ID                   số tài khoản QC (không có "act_")
  META_ADS_TOKEN                       System User token có ads_management (hoặc user token)
  META_IG_USER_ID                      (tuỳ chọn) ID tài khoản Instagram để QC chạy cả Instagram
Nhắm mục tiêu mặc định: Việt Nam, 28–55 tuổi, Advantage+ audience – sửa trong TARGETING.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "video" / "out" / "danh-sach-dang.json"
STATE = ROOT / "video" / "out" / "trang-thai-dang.json"
VER = "v21.0"
GRAPH, GRAPH_VIDEO = f"https://graph.facebook.com/{VER}", f"https://graph-video.facebook.com/{VER}"
VN = timezone(timedelta(hours=7))
TARGETING = {
    "geo_locations": {"countries": ["VN"]},
    "age_min": 28, "age_max": 55,
    "targeting_automation": {"advantage_audience": 1},
}


def env(name: str, required: bool = True) -> str:
    v = os.environ.get(name, "")
    if required and not v:
        sys.exit(f"Thiếu biến môi trường {name} (xem đầu file).")
    return v


def load_state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def api(method: str, url: str, real: bool, **kw) -> dict:
    shown = {k: v for k, v in (kw.get("data") or kw.get("params") or {}).items() if "token" not in k}
    if not real:
        print(f"  [chạy thử] {method} {url.replace(GRAPH, '').replace(GRAPH_VIDEO, '')} {json.dumps(shown, ensure_ascii=False)[:300]}")
        return {"id": f"THU_{int(time.time() * 1000) % 10**8}"}
    r = requests.request(method, url, timeout=600, **kw)
    res = r.json()
    if "error" in res:
        sys.exit(f"Lỗi Meta API: {res['error'].get('message')} ({url})")
    return res


# ---------------- đăng bài ----------------
def cmd_dang(a) -> None:
    items, st = json.loads(LIST.read_text(encoding="utf-8")), load_state()
    page, token = env("META_PAGE_ID", a.that), env("META_PAGE_TOKEN", a.that)
    slots = [s.strip() for s in (a.lich or "").split(",") if s.strip()]
    todo = [it for it in items if it["sku"] not in st]
    for i, it in enumerate(todo):
        data = {"description": it["caption"], "access_token": token}
        when = ""
        if i < len(slots):
            t = datetime.strptime(slots[i], "%Y-%m-%d %H:%M").replace(tzinfo=VN)
            if t < datetime.now(VN) + timedelta(minutes=15):
                sys.exit(f"Mốc {slots[i]} phải sau hiện tại ít nhất 15 phút")
            data.update(published="false", scheduled_publish_time=str(int(t.timestamp())))
            when = f" (hẹn {slots[i]})"
        print(f"▶ Đăng {it['sku']}{when}")
        if a.that:
            with open(ROOT / it["video"], "rb") as f:
                res = api("POST", f"{GRAPH_VIDEO}/{page}/videos", True, data=data, files={"source": f})
        else:
            res = api("POST", f"{GRAPH_VIDEO}/{page or '<PAGE_ID>'}/videos", False, data=data)
        st[it["sku"]] = {"video_id": res["id"], "dang_luc": datetime.now(VN).isoformat(timespec="minutes"), "hen": when.strip(" ()")}
        if a.that:
            save_state(st)
    print(f"✔ {len(todo)} video {'đã gửi lên Page' if a.that else '(chạy thử – thêm --that để đăng thật)'}")


# ---------------- tạo quảng cáo ----------------
def cmd_ads(a) -> None:
    items, st = {it["sku"]: it for it in json.loads(LIST.read_text(encoding="utf-8"))}, load_state()
    act, token, page = f"act_{env('META_AD_ACCOUNT_ID', a.that)}", env("META_ADS_TOKEN", a.that), env("META_PAGE_ID", a.that)
    ig = env("META_IG_USER_ID", False)
    status = "ACTIVE" if a.bat else "PAUSED"
    todo = [s for s, v in st.items() if "ad_id" not in v] if st else list(items)
    if not todo:
        return print("Không có video mới cần tạo quảng cáo. Chạy 'dang' trước.")
    name = f"LiaCasa | Nhắn tin | {datetime.now(VN):%d/%m}"
    camp = api("POST", f"{GRAPH}/{act}/campaigns", a.that, data={
        "name": name, "objective": "OUTCOME_ENGAGEMENT", "status": status,
        "special_ad_categories": "[]", "is_adset_budget_sharing_enabled": "false", "access_token": token})
    print(f"▶ Chiến dịch {name} -> {camp['id']} ({status})")
    for sku in todo:
        it, v = items.get(sku), st.get(sku, {})
        if not it:
            continue
        thumb = ROOT / it["thumbnail"]
        if a.that:
            with open(thumb, "rb") as f:
                img = api("POST", f"{GRAPH}/{act}/adimages", True, data={"access_token": token}, files={"filename": f})
            image_hash = next(iter(img["images"].values()))["hash"]
        else:
            image_hash = "HASH_THU"
        adset = api("POST", f"{GRAPH}/{act}/adsets", a.that, data={
            "name": f"{sku} | VN 28-55", "campaign_id": camp["id"], "daily_budget": str(a.ngan_sach),
            "billing_event": "IMPRESSIONS", "optimization_goal": "CONVERSATIONS", "destination_type": "MESSENGER",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP", "promoted_object": json.dumps({"page_id": page}),
            "targeting": json.dumps(TARGETING), "status": status, "access_token": token})
        spec = {"page_id": page, "video_data": {
            "video_id": v.get("video_id", "VIDEO_ID"), "image_hash": image_hash, "message": it["caption"],
            "call_to_action": {"type": "MESSAGE_PAGE", "value": {"app_destination": "MESSENGER"}}}}
        if ig:
            spec["instagram_user_id"] = ig
        creative = api("POST", f"{GRAPH}/{act}/adcreatives", a.that, data={
            "name": f"{sku} video", "object_story_spec": json.dumps(spec, ensure_ascii=False), "access_token": token})
        ad = api("POST", f"{GRAPH}/{act}/ads", a.that, data={
            "name": f"{sku} | video 15s", "adset_id": adset["id"], "creative": json.dumps({"creative_id": creative["id"]}),
            "status": status, "access_token": token})
        print(f"  ✔ {sku}: nhóm QC {adset['id']} · QC {ad['id']} · {a.ngan_sach:,}đ/ngày".replace(",", "."))
        if a.that:
            st.setdefault(sku, {}).update(campaign_id=camp["id"], adset_id=adset["id"], ad_id=ad["id"])
            save_state(st)
    if not a.bat:
        print("ℹ Quảng cáo đang TẠM DỪNG – vào Ads Manager duyệt rồi bật, hoặc chạy lại với --bat.")


# ---------------- tự tối ưu ----------------
def cmd_toi_uu(a) -> None:
    act, token = f"act_{env('META_AD_ACCOUNT_ID')}", env("META_ADS_TOKEN")
    res = requests.get(f"{GRAPH}/{act}/ads", timeout=60, params={
        "fields": "id,name,effective_status,insights.date_preset(last_3d){spend,actions}",
        "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
        "limit": 200, "access_token": token}).json()
    if "error" in res:
        sys.exit(f"Lỗi Meta API: {res['error'].get('message')}")
    for ad in res.get("data", []):
        ins = (ad.get("insights") or {}).get("data", [{}])[0]
        spend = float(ins.get("spend", 0))
        msgs = sum(int(x["value"]) for x in ins.get("actions", [])
                   if x["action_type"] == "onsite_conversion.messaging_conversation_started_7d")
        cpl = spend / msgs if msgs else float("inf")
        verdict = "giữ"
        if spend >= a.chi_toi_thieu and cpl > a.cpl_toi_da:
            verdict = "TẠM DỪNG"
            api("POST", f"{GRAPH}/{ad['id']}", a.that, data={"status": "PAUSED", "access_token": token})
        cpl_s = "—" if msgs == 0 else f"{cpl:,.0f}đ".replace(",", ".")
        print(f"{ad['name'][:40]:40} chi {spend:>12,.0f}đ · {msgs:>3} tin · CPL {cpl_s:>10} -> {verdict}".replace(",", "."))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dang"); d.add_argument("--lich"); d.add_argument("--that", action="store_true")
    s = sub.add_parser("ads"); s.add_argument("--ngan-sach", type=int, default=200000)
    s.add_argument("--bat", action="store_true"); s.add_argument("--that", action="store_true")
    t = sub.add_parser("toi-uu"); t.add_argument("--cpl-toi-da", type=int, default=250000)
    t.add_argument("--chi-toi-thieu", type=int, default=300000); t.add_argument("--that", action="store_true")
    a = ap.parse_args()
    {"dang": cmd_dang, "ads": cmd_ads, "toi-uu": cmd_toi_uu}[a.cmd](a)


if __name__ == "__main__":
    main()
