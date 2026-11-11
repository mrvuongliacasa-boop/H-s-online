#!/usr/bin/env python3
"""Xuất catalogue PDF Lia Casa (khổ A4) từ landing/catalog.json.

  python3 tools/build_catalog.py        # cập nhật dữ liệu trước
  python3 tools/make_catalogue.py       # -> catalogue/LiaCasa-Catalogue-co-gia.pdf
                                        #    catalogue/LiaCasa-Catalogue-khong-gia.pdf (gửi KTS / hàng chờ giá)
Cần Node + Playwright (đã có sẵn trong môi trường) để in PDF.
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "landing" / "catalog.json"
OUT = ROOT / "catalogue"
CONTACT = {"hotline": "0900 000 000", "zalo": "0900000000", "web": "liacasa.vn", "showroom": "[Địa chỉ showroom]"}
PER_PAGE = 4

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; }
body { font-family: "DejaVu Sans", sans-serif; color: #2b2620; }
.page { width: 210mm; height: 297mm; padding: 16mm; page-break-after: always; position: relative; background: #faf7f2; }
.cover { background: #2b2620; color: #faf7f2; display: flex; flex-direction: column; justify-content: center; }
.cover h1 { font-family: "DejaVu Serif", serif; font-size: 52pt; letter-spacing: 2px; }
.cover .sub { letter-spacing: 6px; text-transform: uppercase; color: #c9a46b; margin-top: 6mm; font-size: 12pt; }
.cover .meta { position: absolute; bottom: 16mm; left: 16mm; right: 16mm; display: flex; justify-content: space-between; font-size: 10pt; color: #b3a998; }
.cat { font-family: "DejaVu Serif", serif; font-size: 24pt; margin-bottom: 2mm; }
.rule { height: 1px; background: #c9a46b; margin-bottom: 8mm; width: 40mm; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8mm; }
.card { background: #fff; border: 1px solid #e7dfd3; border-radius: 4mm; overflow: hidden; }
.card img { width: 100%; height: 68mm; object-fit: cover; display: block; }
.card .b { padding: 4mm 5mm 5mm; height: 46mm; display: flex; flex-direction: column; gap: 1.2mm; }
.tag { font-size: 8pt; color: #8a6a3f; text-transform: uppercase; letter-spacing: 1px; }
.name { font-weight: bold; font-size: 11.5pt; line-height: 1.25; }
.spec { font-size: 8.5pt; color: #6f665b; line-height: 1.35; }
.price { margin-top: auto; font-weight: bold; font-size: 13pt; }
.price del { color: #9a9086; font-weight: normal; font-size: 9pt; margin-left: 2mm; }
.price.sale { color: #b4442f; }
.price.later { color: #8a6a3f; font-size: 10.5pt; }
.foot { position: absolute; bottom: 8mm; left: 16mm; right: 16mm; display: flex; justify-content: space-between; font-size: 8pt; color: #9a9086; }
.back { background: #2b2620; color: #faf7f2; display: flex; flex-direction: column; justify-content: center; gap: 6mm; font-size: 13pt; }
.back h2 { font-family: "DejaVu Serif", serif; font-size: 30pt; color: #c9a46b; }
.back .small { font-size: 9pt; color: #b3a998; margin-top: 10mm; }
"""


def vnd(n: int) -> str:
    return f"{n:,}".replace(",", ".") + " đ"


def price_html(p: dict, co_gia: bool) -> str:
    if not co_gia:
        return '<div class="price later">Liên hệ báo giá</div>'
    if p["loai_gia"] == "cap_nhat_sau":
        tu = f" · dự kiến từ {vnd(p['gia_du_kien_tu'])}" if p.get("gia_du_kien_tu") else ""
        return f'<div class="price later">Giá theo lô nhập{tu}</div>'
    if p.get("gia_khuyen_mai"):
        return f'<div class="price sale">{vnd(p["gia_khuyen_mai"])}<del>{vnd(p["gia_niem_yet"])}</del></div>'
    return f'<div class="price">{vnd(p["gia_niem_yet"])}</div>'


def card(p: dict, co_gia: bool) -> str:
    e = html.escape
    img = p["anh"] if p["anh"].startswith("http") else (ROOT / "landing" / p["anh"]).as_uri()
    spec = " · ".join(x for x in [p.get("chat_lieu"), p.get("kich_thuoc"), f"Giao {p['thoi_gian_giao']}" if p.get("thoi_gian_giao") else ""] if x)
    return (f'<div class="card"><img src="{e(img)}" alt=""><div class="b">'
            f'<div class="tag">{e(p["xuat_xu"])} · {e(p["sku"])}</div><div class="name">{e(p["ten"])}</div>'
            f'<div class="spec">{e(spec)}</div>{price_html(p, co_gia)}</div></div>')


def build_html(data: dict, co_gia: bool) -> str:
    today = date.today().strftime("%d/%m/%Y")
    pages = [f'<section class="page cover"><h1>LIA CASA</h1><div class="sub">Nội thất nhập khẩu · Catalogue</div>'
             f'<div class="meta"><span>Ý · Tây Ban Nha · Bắc Âu</span><span>Cập nhật {today}</span></div></section>']
    cats: dict[str, list] = {}
    for p in data["san_pham"]:
        cats.setdefault(p["danh_muc"], []).append(p)
    n = 1
    for cat, items in cats.items():
        for i in range(0, len(items), PER_PAGE):
            n += 1
            cards = "".join(card(p, co_gia) for p in items[i:i + PER_PAGE])
            pages.append(f'<section class="page"><div class="cat">{html.escape(cat)}</div><div class="rule"></div>'
                         f'<div class="grid">{cards}</div><div class="foot"><span>Lia Casa – Nội thất nhập khẩu · {CONTACT["web"]}</span>'
                         f'<span>Hotline {CONTACT["hotline"]} · {n}</span></div></section>')
    note = ("Giá có hiệu lực tại thời điểm phát hành, có thể thay đổi theo tỷ giá và lô nhập. "
            "Báo giá chính thức gửi qua Zalo/email, hiệu lực 7 ngày.") if co_gia else "Liên hệ để nhận báo giá theo dự án và chính sách đối tác."
    pages.append(f'<section class="page back"><h2>Liên hệ Lia Casa</h2><div>Hotline / Zalo: {CONTACT["hotline"]}</div>'
                 f'<div>Website: {CONTACT["web"]}</div><div>Showroom: {html.escape(CONTACT["showroom"])}</div>'
                 f'<div>Thiết kế 3D miễn phí · Giao & lắp đặt · Bảo hành dài hạn</div><div class="small">{note}</div></section>')
    return f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'


PDF_JS = """
const { chromium } = require('playwright');
(async () => {
  const [src, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + src, { waitUntil: 'load' });
  await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true });
  await b.close();
})();
"""


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    js = OUT / ".in-pdf.js"
    js.write_text(PDF_JS, encoding="utf-8")
    try:
        for co_gia, name in ((True, "co-gia"), (False, "khong-gia")):
            src = OUT / f"catalogue-{name}.html"
            src.write_text(build_html(data, co_gia), encoding="utf-8")
            pdf = OUT / f"LiaCasa-Catalogue-{name}.pdf"
            subprocess.run(["node", str(js), str(src), str(pdf)], check=True)
            print(f"✔ {pdf.relative_to(ROOT)}")
    finally:
        js.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
