#!/usr/bin/env python3
"""Tự dựng video quảng cáo dọc 9:16 (1080x1920, 15s) cho từng sản phẩm + nội dung bài đăng.

  python3 tools/make_videos.py                 # tất cả SKU
  python3 tools/make_videos.py LC-SF-001 ...   # chỉ các SKU chỉ định
  python3 tools/make_videos.py --top 4         # 4 SKU đầu (ưu tiên hàng có giá, có KM)

Đầu vào : landing/catalog.json (chạy build_catalog.py trước), ảnh landing/anh/<SKU>.jpg
          video/nhac-nen.mp3 (tuỳ chọn – nhạc bản quyền của bạn; không có thì video im lặng)
Đầu ra  : video/out/<SKU>.mp4, video/out/<SKU>.txt (caption), video/out/danh-sach-dang.json
          (danh sách cho tools/dang_bai_ads.py tự đăng & chạy ads)

Kịch bản 15s: 0–3s hook · 3–9s sản phẩm + thông số · 9–12.5s giá · 12.5–15s kêu gọi nhắn tin.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "landing" / "catalog.json"
OUT = ROOT / "video" / "out"
MUSIC = ROOT / "video" / "nhac-nen.mp3"
W, H, FPS, DUR = 1080, 1920, 25, 15.0
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
ACCENT, INK, CREAM, SALE = (201, 164, 107), (30, 26, 22), (250, 247, 242), (226, 119, 95)
BRAND = {"ten": "LIA CASA", "phu": "NỘI THẤT NHẬP KHẨU", "hotline": "0900 000 000",
         "landing": "https://liacasa.vn", "hashtag": "#liacasa #noithatnhapkhau #noithatcaocap #sofa #thietkenoithat"}

HOOKS_CO_GIA = ["{dm} {xx} thật – giá bao nhiêu?", "Đừng mua {dm_l} trước khi xem video này", "Hàng {xx} về kho – số lượng có hạn"]
HOOKS_CAP_NHAT = ["Mẫu này chỉ đặt được theo lô nhập từ {xx}", "{dm} đặt riêng theo kích thước nhà bạn", "Lô hàng {xx} tháng này đang mở đặt"]


def vnd(n: int) -> str:
    return f"{n:,}".replace(",", ".") + "đ"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, f, max_w: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        t = f"{cur} {word}".strip()
        if draw.textlength(t, font=f) <= max_w:
            cur = t
        else:
            lines.append(cur); cur = word
    return lines + ([cur] if cur else [])


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def load_photo(p: dict) -> Image.Image:
    src = p["anh"]
    path = ROOT / "landing" / src if not src.startswith("http") else None
    if path and path.exists():
        return Image.open(path).convert("RGB")
    raise SystemExit(f"Thiếu ảnh cho {p['sku']}: đặt file vào landing/anh/{p['sku']}.jpg")


def cover(img: Image.Image, w: int, h: int, zoom: float, dx: float = 0.0) -> Image.Image:
    """Cắt ảnh lấp đầy khung w×h, phóng to `zoom`, trượt ngang dx (-1..1)."""
    s = max(w / img.width, h / img.height) * zoom
    rw, rh = int(img.width * s), int(img.height * s)
    im = img.resize((rw, rh), Image.LANCZOS)
    x = int((rw - w) / 2 * (1 + dx)); y = (rh - h) // 2
    return im.crop((x, y, x + w, y + h))


def text_block(d, lines, f, y, fill, cx=W // 2, gap=1.18):
    for ln in lines:
        d.text((cx, y), ln, font=f, fill=fill, anchor="mt")
        y += int(f.size * gap)
    return y


def frame(p: dict, photo: Image.Image, bg: Image.Image, hook: str, t: float) -> Image.Image:
    # nền: ảnh mờ toàn khung + ảnh sắc nét vuông ở giữa (Ken Burns)
    img = bg.copy()
    z = 1.0 + 0.08 * (t / DUR)
    sq = cover(photo, W, W, z, dx=0.15 * (t / DUR) - 0.075)
    img.paste(sq, (0, (H - W) // 2 - 80))
    d = ImageDraw.Draw(img, "RGBA")
    # dải thương hiệu trên cùng
    d.rectangle([0, 0, W, 170], fill=(*INK, 215))
    d.text((W // 2, 50), BRAND["ten"], font=font(SERIF, 54), fill=CREAM, anchor="mt")
    d.text((W // 2, 120), BRAND["phu"], font=font(REG, 26), fill=ACCENT, anchor="mt")

    if t < 3.0:  # HOOK
        a = int(235 * ease(t / 0.4))
        f = font(BOLD, 76)
        lines = wrap(d, hook.upper(), f, W - 140)
        bh = len(lines) * int(76 * 1.18) + 80
        top = 300
        d.rounded_rectangle([50, top, W - 50, top + bh], 36, fill=(*INK, a))
        text_block(d, lines, f, top + 40, (*CREAM, int(255 * ease(t / 0.4))))
    if 3.0 <= t < 15.0:  # tên + thông số ở dưới
        a = ease((t - 3.0) / 0.5)
        y0 = 1400 + int(40 * (1 - a))
        d.rectangle([0, y0 - 30, W, H], fill=(*INK, int(225 * a)))
        f = font(BOLD, 58)
        y = text_block(d, wrap(d, p["ten"].replace(" (MẪU)", ""), f, W - 120)[:2], f, y0, (*CREAM, int(255 * a)))
        spec = " · ".join(x for x in [p.get("xuat_xu") and f"Nhập khẩu {p['xuat_xu']}", p.get("chat_lieu")] if x)
        fs = font(REG, 34)
        y = text_block(d, wrap(d, spec, fs, W - 140)[:2], fs, y + 14, (*ACCENT, int(255 * a)))
        if t >= 9.0:  # GIÁ
            b = ease((t - 9.0) / 0.45)
            if p["loai_gia"] == "co_san":
                gia = p.get("gia_khuyen_mai") or p["gia_niem_yet"]
                txt, col = vnd(gia), (SALE if p.get("gia_khuyen_mai") else CREAM)
                sub = f"Giá gốc {vnd(p['gia_niem_yet'])}" if p.get("gia_khuyen_mai") else f"Giao {p.get('thoi_gian_giao', '')}"
            else:
                txt, col = "GIÁ THEO LÔ NHẬP", ACCENT
                sub = f"Dự kiến từ {vnd(p['gia_du_kien_tu'])}" if p.get("gia_du_kien_tu") else "Báo giá trong 15 phút"
            cy = 1180
            d.rounded_rectangle([140, cy, W - 140, cy + 190], 30, fill=(*INK, int(235 * b)))
            d.text((W // 2, cy + 30), txt, font=font(BOLD, 72), fill=(*col, int(255 * b)), anchor="mt")
            d.text((W // 2, cy + 125), sub, font=font(REG, 32), fill=(*CREAM, int(230 * b)), anchor="mt")
        if t >= 12.5:  # CTA
            c = ease((t - 12.5) / 0.4)
            pulse = 1 + 0.03 * abs(((t * 2) % 2) - 1)
            bw, bh = int(760 * pulse), int(120 * pulse)
            x0, y1 = (W - bw) // 2, 1745
            d.rounded_rectangle([x0, y1, x0 + bw, y1 + bh], 60, fill=(*ACCENT, int(255 * c)))
            d.text((W // 2, y1 + bh // 2), "NHẮN TIN NHẬN BÁO GIÁ", font=font(BOLD, 44), fill=(*INK, int(255 * c)), anchor="mm")
    return img


def caption(p: dict, hook: str) -> str:
    link = f"{BRAND['landing']}/?utm_source=facebook&utm_medium=video&utm_campaign=auto&utm_content={p['sku']}#{p['sku']}"
    if p["loai_gia"] == "co_san":
        gia = p.get("gia_khuyen_mai") or p["gia_niem_yet"]
        price = f"💰 Giá: {vnd(gia)}" + (f" (giá gốc {vnd(p['gia_niem_yet'])})" if p.get("gia_khuyen_mai") else "")
        price += f"\n🚚 Có sẵn – giao {p.get('thoi_gian_giao', '')}"
    else:
        price = "💰 Giá theo lô nhập" + (f" – dự kiến từ {vnd(p['gia_du_kien_tu'])}" if p.get("gia_du_kien_tu") else "")
        price += f"\n📦 Đặt theo lô – giao {p.get('thoi_gian_giao', '')}"
    return (f"{hook} 👇\n\n✨ {p['ten'].replace(' (MẪU)', '')}\n🇪🇺 Nhập khẩu {p['xuat_xu']} · {p.get('chat_lieu', '')}\n"
            f"📐 {p.get('kich_thuoc', '')}\n{price}\n\n{p.get('mo_ta', '')}\n\n"
            f"📩 Nhắn tin ngay để nhận báo giá trong 15 phút\n☎️ Hotline/Zalo: {BRAND['hotline']}\n🔗 Xem catalog: {link}\n\n{BRAND['hashtag']}")


def render(p: dict, idx: int) -> dict:
    photo = load_photo(p)
    bg = cover(photo, W, H, 1.0).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), INK), 0.45)
    hooks = HOOKS_CO_GIA if p["loai_gia"] == "co_san" else HOOKS_CAP_NHAT
    hook = hooks[idx % len(hooks)].format(dm=p["danh_muc"], dm_l=p["danh_muc"].lower(), xx=p["xuat_xu"])
    out = OUT / f"{p['sku']}.mp4"
    audio = (["-stream_loop", "-1", "-i", str(MUSIC)] if MUSIC.exists()
             else ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           *audio, "-map", "0:v", "-map", "1:a", "-t", str(DUR), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k",
           "-af", f"afade=t=in:d=0.5,afade=t=out:st={DUR - 1}:d=1", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        proc.stdin.write(frame(p, photo, bg, hook, i / FPS).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg lỗi khi dựng {p['sku']}")
    cap = caption(p, hook)
    (OUT / f"{p['sku']}.txt").write_text(cap, encoding="utf-8")
    thumb = OUT / f"{p['sku']}.jpg"
    frame(p, photo, bg, hook, 10.0).convert("RGB").save(thumb, quality=85)
    print(f"✔ {out.relative_to(ROOT)}")
    return {"sku": p["sku"], "video": str(out.relative_to(ROOT)), "thumbnail": str(thumb.relative_to(ROOT)),
            "caption": cap, "loai_gia": p["loai_gia"]}


def main(argv: list[str]) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))["san_pham"]
    if "--top" in argv:
        n = int(argv[argv.index("--top") + 1])
        data = sorted(data, key=lambda p: (p["loai_gia"] != "co_san", not p.get("gia_khuyen_mai")))[:n]
    elif argv:
        want = set(argv); data = [p for p in data if p["sku"] in want]
    OUT.mkdir(parents=True, exist_ok=True)
    items = [render(p, i) for i, p in enumerate(data)]
    (OUT / "danh-sach-dang.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ {len(items)} video + caption -> {OUT.relative_to(ROOT)}/danh-sach-dang.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
