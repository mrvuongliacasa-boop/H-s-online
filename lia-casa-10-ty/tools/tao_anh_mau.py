#!/usr/bin/env python3
"""Tạo ảnh MẪU (placeholder) 1080x1080 cho các SKU chưa có ảnh thật trong landing/anh/.
Ảnh thật: chỉ cần chép đè landing/anh/<SKU>.jpg rồi chạy lại các công cụ."""
import csv, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TONES = [((214, 196, 170), (140, 110, 75)), ((200, 205, 200), (90, 100, 95)), ((225, 210, 195), (150, 95, 70))]

def make(path: Path, title: str, cat: str, i: int) -> None:
    a, b = TONES[i % len(TONES)]
    img = Image.new("RGB", (1080, 1080), a)
    d = ImageDraw.Draw(img)
    for y in range(1080):  # nền chuyển màu
        t = y / 1079
        d.line([(0, y), (1080, y)], fill=tuple(int(a[k] * (1 - t) + b[k] * t * 0.6 + a[k] * t * 0.4) for k in range(3)))
    d.rectangle([0, 760, 1080, 1080], fill=tuple(max(0, c - 40) for c in a))  # sàn
    # khối nội thất cách điệu
    if cat in ("Sofa", "Ghế"):
        d.rounded_rectangle([200, 520, 880, 760], 40, fill=b); d.rounded_rectangle([200, 420, 880, 560], 40, fill=tuple(c + 20 for c in b))
    elif cat in ("Bàn ăn", "Bàn trà"):
        d.rectangle([180, 520, 900, 560], fill=b); d.rectangle([230, 560, 260, 760], fill=b); d.rectangle([820, 560, 850, 760], fill=b)
    elif cat == "Giường":
        d.rounded_rectangle([150, 380, 930, 560], 30, fill=b); d.rectangle([150, 560, 930, 760], fill=tuple(c + 25 for c in b))
    else:
        d.line([(540, 0), (540, 300)], fill=b, width=6); d.ellipse([340, 280, 740, 560], fill=b)
    f = ImageFont.truetype(FONT, 44); s = ImageFont.truetype(FONT, 30)
    d.text((540, 860), title, font=f, fill=(255, 255, 255), anchor="mm")
    d.text((540, 930), "ẢNH MẪU – thay bằng ảnh thật", font=s, fill=(255, 255, 255), anchor="mm")
    img.save(path, quality=88)

def main() -> None:
    rows = list(csv.DictReader((ROOT / "catalog" / "catalog.csv").open(encoding="utf-8-sig")))
    for i, r in enumerate(rows):
        p = ROOT / "landing" / "anh" / f"{r['sku']}.jpg"
        if p.exists() and "--ghi-de" not in sys.argv:
            continue
        make(p, r["ten"].replace(" (MẪU)", "")[:34], r["danh_muc"], i)
        print("tạo", p.relative_to(ROOT))

if __name__ == "__main__":
    main()
