#!/usr/bin/env python3
"""Sinh dữ liệu catalog Lia Casa từ catalog/catalog.csv.

Đầu ra:
  landing/catalog.json             -> dữ liệu cho landing page
  catalog/feed-meta-tiktok.csv     -> feed Meta Commerce / TikTok Catalog (chỉ SKU đã có giá)
  catalog/bao-gia-cho-cap-nhat.csv -> danh sách SKU "giá cập nhật sau" cho đội sale

Chạy:  python3 tools/build_catalog.py [--base-url https://liacasa.vn]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "catalog" / "catalog.csv"
OUT_JSON = ROOT / "landing" / "catalog.json"
OUT_FEED = ROOT / "catalog" / "feed-meta-tiktok.csv"
OUT_QUOTE = ROOT / "catalog" / "bao-gia-cho-cap-nhat.csv"

BRAND = "Lia Casa"
LOAI_GIA = {"co_san", "cap_nhat_sau"}
REQUIRED = ["sku", "ten", "danh_muc", "xuat_xu", "loai_gia", "anh", "ngay_cap_nhat"]


def to_int(value: str) -> int | None:
    value = (value or "").replace(".", "").replace(",", "").replace(" ", "").strip()
    return int(value) if value.isdigit() else None


def load(path: Path) -> tuple[list[dict], list[str]]:
    rows, errors, seen = [], [], set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for line_no, raw in enumerate(csv.DictReader(f), start=2):
            row = {k: (v or "").strip() for k, v in raw.items()}
            where = f"dòng {line_no} ({row.get('sku') or '?'})"
            missing = [c for c in REQUIRED if not row.get(c)]
            if missing:
                errors.append(f"{where}: thiếu {', '.join(missing)}")
                continue
            if row["sku"] in seen:
                errors.append(f"{where}: trùng SKU")
                continue
            seen.add(row["sku"])
            if row["loai_gia"] not in LOAI_GIA:
                errors.append(f"{where}: loai_gia phải là co_san hoặc cap_nhat_sau")
                continue
            for key in ("gia_niem_yet", "gia_khuyen_mai", "gia_du_kien_tu", "ton_kho"):
                row[key] = to_int(row.get(key, ""))
            if row["loai_gia"] == "co_san" and not row["gia_niem_yet"]:
                errors.append(f"{where}: hàng 'co_san' bắt buộc có gia_niem_yet")
                continue
            km = row["gia_khuyen_mai"]
            if km and row["gia_niem_yet"] and km >= row["gia_niem_yet"]:
                errors.append(f"{where}: gia_khuyen_mai phải nhỏ hơn gia_niem_yet (đã bỏ KM)")
                row["gia_khuyen_mai"] = None
            rows.append(row)
    return rows, errors


def write_json(rows: list[dict]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "thuong_hieu": BRAND,
        "cap_nhat": max((r["ngay_cap_nhat"] for r in rows), default=""),
        "san_pham": rows,
    }
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_feed(rows: list[dict], base_url: str) -> int:
    cols = ["id", "title", "description", "availability", "condition", "price",
            "sale_price", "link", "image_link", "brand", "product_type"]
    count = 0
    with OUT_FEED.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            if r["loai_gia"] != "co_san":
                continue  # Meta/TikTok bắt buộc có giá -> hàng "cập nhật sau" chạy bằng Lead Ads
            w.writerow({
                "id": r["sku"],
                "title": r["ten"][:150],
                "description": (r.get("mo_ta") or r["ten"])[:5000],
                "availability": "in stock" if (r["ton_kho"] or 0) > 0 else "available for order",
                "condition": "new",
                "price": f"{r['gia_niem_yet']} VND",
                "sale_price": f"{r['gia_khuyen_mai']} VND" if r["gia_khuyen_mai"] else "",
                "link": r.get("link") or f"{base_url.rstrip('/')}/#{r['sku']}",
                "image_link": r["anh"],
                "brand": BRAND,
                "product_type": r["danh_muc"],
            })
            count += 1
    return count


def write_quote_list(rows: list[dict]) -> int:
    cols = ["sku", "ten", "danh_muc", "xuat_xu", "gia_du_kien_tu", "thoi_gian_giao", "ngay_cap_nhat"]
    items = [r for r in rows if r["loai_gia"] == "cap_nhat_sau"]
    with OUT_QUOTE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(items)
    return len(items)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="https://liacasa.vn", help="URL landing page dùng cho link trong feed")
    args = ap.parse_args()

    rows, errors = load(SRC)
    write_json(rows)
    n_feed = write_feed(rows, args.base_url)
    n_quote = write_quote_list(rows)

    print(f"✔ {len(rows)} sản phẩm hợp lệ -> {OUT_JSON.relative_to(ROOT)}")
    print(f"✔ {n_feed} SKU giá sẵn -> {OUT_FEED.relative_to(ROOT)}")
    print(f"✔ {n_quote} SKU giá cập nhật sau -> {OUT_QUOTE.relative_to(ROOT)}")
    for e in errors:
        print(f"⚠ {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
