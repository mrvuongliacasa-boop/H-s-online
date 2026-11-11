"""Bộ não chatbot Lia Casa – dùng chung cho Facebook Messenger, Instagram DM và Zalo OA.

Đầu vào: tin nhắn của khách + trạng thái hội thoại (dict, do server lưu theo từng khách).
Đầu ra : danh sách Reply(text, options) – server tự chuyển thành nút bấm (FB) hoặc menu số (Zalo).
Dữ liệu: chatbot/kich-ban.json (kịch bản, FAQ) + landing/catalog.json (sản phẩm, giá).
Nguyên tắc: KHÔNG tự bịa giá – chỉ đọc từ catalog; hàng "giá cập nhật sau" luôn xin SĐT để báo giá.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = json.loads((ROOT / "chatbot" / "kich-ban.json").read_text(encoding="utf-8"))
V = SCRIPT["bien"]
PHONE_RE = re.compile(r"(?:\+?84|0)(?:[\s.\-]?\d){9}\b")

ROOMS = {"phong khach": ["Sofa", "Bàn trà", "Ghế", "Đèn"], "phong an": ["Bàn ăn"], "phong ngu": ["Giường"]}
MENU = [("🛋 Xem catalog", "catalog"), ("💰 Hỏi giá", "hoi_gia"), ("📐 Thiết kế 3D miễn phí", "thiet_ke"),
        ("📍 Đặt lịch showroom", "showroom"), ("👩‍💼 Gặp nhân viên", "handoff")]
FAQ_KEYS = {"bao_hanh": ["bao hanh"], "giao_hang": ["giao hang", "ship", "van chuyen", "bao lau"],
            "tra_gop": ["tra gop", "gop"], "xuat_xu": ["xuat xu", "co cq", "chinh hang", "hang that", "nhap khau"],
            "dat_coc": ["coc", "dat truoc"], "doi_tra": ["doi tra", "tra hang", "doi hang"]}
STOP = {"cho", "mau", "gia", "the", "nao", "khong", "co"}  # từ phổ biến, không dùng để nhận diện mẫu
BUDGETS = ["Dưới 30 triệu", "30–80 triệu", "80–200 triệu", "Trên 200 triệu"]


@dataclass
class Reply:
    text: str
    options: list[tuple[str, str]] = field(default_factory=list)  # (nhãn, payload)
    image: str | None = None


def strip_vn(s: str) -> str:
    """'Giá Sofa ĐỎ' -> 'gia sofa do' (bỏ dấu, chữ thường)."""
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()


def has(t: str, kws: list[str]) -> bool:
    """Có cụm từ khoá nào xuất hiện nguyên từ trong t."""
    return any(re.search(rf"\b{re.escape(k)}\b", t) for k in kws)


def vnd(n: int) -> str:
    return f"{n:,}".replace(",", ".") + " đ"


def load_products() -> list[dict]:
    return json.loads((ROOT / "landing" / "catalog.json").read_text(encoding="utf-8"))["san_pham"]


class Bot:
    def __init__(self, products: list[dict] | None = None):
        self.products = products if products is not None else load_products()
        freq: dict[str, int] = {}
        for p in self.products:
            for w in set(self._words(p)):
                freq[w] = freq.get(w, 0) + 1
        self._unique = {w for w, n in freq.items() if n == 1 and len(w) >= 4}

    @staticmethod
    def _words(p: dict) -> list[str]:
        return [w for w in strip_vn(p["ten"].replace("(MẪU)", "")).split() if len(w) > 2 and w not in STOP]

    # ---------- tra cứu sản phẩm ----------
    def find_product(self, text: str) -> dict | None:
        t = strip_vn(text)
        for p in self.products:
            if p["sku"].lower() in t:
                return p
        best, key = None, (0, 0)
        for p in self.products:
            hit = [w for w in self._words(p) if re.search(rf"\b{re.escape(w)}\b", t)]
            k = (sum(w in self._unique for w in hit), len(hit))  # ưu tiên tên riêng (VD "milano")
            if k > key:
                best, key = p, k
        # khớp tên riêng chỉ có ở 1 mẫu, hoặc >= 2 từ khớp
        return best if key[0] >= 1 or key[1] >= 2 else None

    def by_category(self, cats: list[str]) -> list[dict]:
        return [p for p in self.products if p["danh_muc"] in cats]

    def price_text(self, p: dict) -> str:
        ten = p["ten"].replace(" (MẪU)", "")
        if p["loai_gia"] == "co_san":
            gia = p.get("gia_khuyen_mai") or p["gia_niem_yet"]
            km = f" (giá gốc {vnd(p['gia_niem_yet'])}, đang ưu đãi)" if p.get("gia_khuyen_mai") else ""
            con = f"Còn {p['ton_kho']} sản phẩm, giao" if (p.get("ton_kho") or 0) > 0 else "Đặt hàng, giao"
            return (f"Mẫu {ten} hiện có giá {vnd(gia)}{km}. {con} {p.get('thoi_gian_giao', '')}. "
                    "Anh/chị muốn em giữ hàng hoặc gửi báo giá chi tiết qua Zalo không ạ?")
        tu = f", dự kiến từ {vnd(p['gia_du_kien_tu'])}" if p.get("gia_du_kien_tu") else ""
        return (f"Mẫu {ten} là hàng đặt theo lô nhập từ {p['xuat_xu']}, giá theo tỷ giá và tuỳ chọn chất liệu/kích thước{tu}. "
                "Anh/chị để lại SĐT/Zalo, chuyên viên gửi báo giá chính xác trong 15 phút ạ.")

    # ---------- xử lý tin nhắn ----------
    def handle(self, text: str, state: dict, payload: str | None = None, name: str = "") -> list[Reply]:
        """Trả về các câu trả lời; cập nhật `state` tại chỗ. state['lead'] được set khi có SĐT."""
        if state.get("handoff"):
            return []  # nhân viên đang trả lời – bot im lặng
        t = strip_vn(text)
        # Zalo/không có nút: khách gõ số chọn menu vừa gửi
        if not payload and t.isdigit() and state.get("last_options"):
            i = int(t) - 1
            if 0 <= i < len(state["last_options"]):
                payload = state["last_options"][i][1]
        if payload:
            return self._remember(state, self._payload(payload, state, name))

        phone = PHONE_RE.search(text or "")
        if phone:
            return self._remember(state, self._got_phone(re.sub(r"\D", "", phone.group()), state))

        step = state.get("step")
        if step == "tk_dien_tich":
            state.setdefault("info", {})["dien_tich"] = text
            state["step"] = "tk_ngan_sach"
            return self._remember(state, [Reply("Ngân sách dự kiến cho nội thất khoảng bao nhiêu ạ?",
                                                [(b, f"ngan_sach:{b}") for b in BUDGETS])])

        if has(t, ["nhan vien", "nguoi that", "goi cho", "goi lai", "khieu nai", "tu van vien"]):
            return self._remember(state, self._payload("handoff", state, name))
        if has(t, ["showroom", "dia chi", "o dau", "xem hang", "ghe tham", "ghe xem"]):
            return self._remember(state, self._payload("showroom", state, name))
        for key, kws in FAQ_KEYS.items():
            if has(t, kws):
                return self._remember(state, [Reply(SCRIPT["faq"][key], [("💰 Hỏi giá", "hoi_gia"), ("🛋 Xem catalog", "catalog")])])
        if has(t, ["thiet ke", "3d", "phoi do", "full nha", "tron goi", "biet thu", "can ho", "nha pho"]):
            return self._remember(state, self._payload("thiet_ke", state, name))

        p = self.find_product(text)
        if p:
            state["sku"] = p["sku"]
            return self._remember(state, self._quote(p, state))
        for room, cats in ROOMS.items():
            if has(t, [room]):
                return self._remember(state, self._carousel(cats))
        for p in self.products:  # khách gõ tên danh mục: "sofa", "giuong"...
            if has(t, [strip_vn(p["danh_muc"])]):
                return self._remember(state, self._carousel([p["danh_muc"]]))
        if has(t, ["gia", "bao nhieu", "bn", "bao gia"]):
            return self._remember(state, self._payload("hoi_gia", state, name))
        if has(t, ["catalog", "catalogue", "mau", "hinh", "hinh anh", "san pham"]):
            return self._remember(state, self._payload("catalog", state, name))
        if has(t, ["cam on", "ok", "oke", "thanks", "da nhan"]):
            return [Reply("Dạ Lia Casa cảm ơn anh/chị ạ ❤️ Cần hỗ trợ thêm cứ nhắn em nhé!")]
        return self._remember(state, self._payload("chao", state, name))

    def _payload(self, pl: str, state: dict, name: str) -> list[Reply]:
        L = SCRIPT["luong"]
        if pl == "chao":
            hello = L["chao"]["tin_nhan"].replace("{first_name}", name or "anh/chị")
            return [Reply(hello, MENU)]
        if pl == "catalog":
            return [Reply(L["catalog"]["tin_nhan"], [("Phòng khách", "room:phong khach"), ("Phòng ăn", "room:phong an"),
                                                    ("Phòng ngủ", "room:phong ngu"), ("🔗 Xem toàn bộ", "link")])]
        if pl.startswith("room:"):
            return self._carousel(ROOMS.get(pl[5:], []))
        if pl == "link":
            return [Reply(f"Toàn bộ catalog & bảng giá: {V['landing']} – anh/chị chọn mẫu rồi bấm 'Gửi danh sách' là em báo giá ngay ạ.")]
        if pl == "hoi_gia":
            if state.get("sku"):
                p = next((x for x in self.products if x["sku"] == state["sku"]), None)
                if p:
                    return self._quote(p, state)
            return [Reply(L["hoi_gia"]["neu_chua_co_sku"], [("🛋 Xem catalog", "catalog")])]
        if pl.startswith("sku:"):
            p = next((x for x in self.products if x["sku"] == pl[4:]), None)
            if p:
                state["sku"] = p["sku"]
                return self._quote(p, state)
        if pl == "thiet_ke":
            state["step"] = "tk_dien_tich"; state["tag"] = "thiet_ke"
            return [Reply("Lia Casa thiết kế 3D miễn phí khi anh/chị chọn nội thất tại showroom ạ. "
                          "Công trình của anh/chị là căn hộ, nhà phố hay biệt thự, diện tích khoảng bao nhiêu m² ạ?")]
        if pl.startswith("ngan_sach:"):
            state.setdefault("info", {})["ngan_sach"] = pl.split(":", 1)[1]
            state["step"] = None
            return [Reply("Dạ em ghi nhận rồi ạ. " + L["xin_sdt"]["tin_nhan"])]
        if pl == "showroom":
            state["tag"] = "hen_showroom"
            return [Reply(L["showroom"]["tin_nhan"].format(**V),
                          [(x, f"lich:{x}") for x in L["showroom"]["lua_chon"]])]
        if pl.startswith("lich:"):
            state.setdefault("info", {})["lich_hen"] = pl[5:]
            return [Reply(f"Dạ em giữ lịch '{pl[5:]}' cho anh/chị. " + L["xin_sdt"]["tin_nhan"])]
        if pl == "giu_hang":
            return [Reply("Dạ em giữ hàng giúp anh/chị trong 24h ạ. " + L["xin_sdt"]["tin_nhan"])]
        if pl == "handoff":
            state["handoff"] = True; state["lead_hot"] = True
            return [Reply(L["handoff"]["tin_nhan"].format(**V))]
        return self._payload("chao", state, name)

    def _quote(self, p: dict, state: dict) -> list[Reply]:
        opts = [("✅ Giữ hàng", "giu_hang")] if p["loai_gia"] == "co_san" else []
        opts += [("📍 Xem hàng ở showroom", "showroom"), ("🛋 Mẫu khác", "catalog")]
        return [Reply(self.price_text(p), opts, image=p.get("anh"))]

    def _carousel(self, cats: list[str]) -> list[Reply]:
        items = self.by_category(cats)[:10]
        if not items:
            return [Reply(f"Mẫu này đang cập nhật, anh/chị xem toàn bộ catalog tại {V['landing']} nhé.")]
        lines = []
        for p in items:
            gia = vnd(p.get("gia_khuyen_mai") or p["gia_niem_yet"]) if p["loai_gia"] == "co_san" else "giá theo lô nhập"
            lines.append(f"• {p['ten'].replace(' (MẪU)', '')} – {gia}")
        return [Reply("Một số mẫu nổi bật:\n" + "\n".join(lines) + "\nAnh/chị bấm mẫu muốn xem giá chi tiết nhé:",
                      [(p["ten"].replace(" (MẪU)", ""), f"sku:{p['sku']}") for p in items[:10]])]

    def _got_phone(self, phone: str, state: dict) -> list[Reply]:
        if phone.startswith("84"):
            phone = "0" + phone[2:]
        info = state.setdefault("info", {})
        hot = state.get("tag") == "hen_showroom" or info.get("ngan_sach") in BUDGETS[2:]
        state["lead"] = {"sdt": phone, "sku": state.get("sku", ""), "tag": "nong" if hot else "am",
                         "nhu_cau": state.get("tag", "hoi_gia"), **info}
        state["step"] = None
        return [Reply(SCRIPT["luong"]["xin_sdt"]["thanh_cong"])]

    @staticmethod
    def _remember(state: dict, replies: list[Reply]) -> list[Reply]:
        last = next((r.options for r in reversed(replies) if r.options), None)
        state["last_options"] = last or []
        return replies


def as_plain_text(r: Reply) -> str:
    """Cho kênh không có nút (Zalo): thêm menu đánh số."""
    if not r.options:
        return r.text
    return r.text + "\n\n" + "\n".join(f"{i}. {label}" for i, (label, _) in enumerate(r.options, 1)) + "\n(Gõ số để chọn)"
