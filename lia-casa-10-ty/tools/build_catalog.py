#!/usr/bin/env python3
"""Sinh dữ liệu catalog Lia Casa từ catalog/catalog.csv.

Đầu ra:
  landing/catalog.json             -> dữ liệu cho landing page
  catalog/feed-meta-tiktok.csv     -> feed Meta Commerce / TikTok Catalog (chỉ SKU đã có giá)
  catalog/bao-gia-cho-cap-nhat.csv -> danh sách SKU "giá cập nhật sau" cho đội sale (kèm giá đề xuất nếu có cost)
  catalog/gia-von-noi-bo.csv       -> giá vốn cập bến & giá đề xuất từng SKU (NỘI BỘ – không công khai)

Giá đề xuất tính từ cost nhà máy theo tham số trong catalog/tham-so-gia.json
(cùng logic file LIA_BAO_GIA_COST): tiền hàng + vận chuyển (m³) + ủy thác + thuế NK
+ CBPG dự phòng + VAT NK, rồi chia (1 - biên lãi - chi phí bán hàng).

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
OUT_COST = ROOT / "catalog" / "gia-von-noi-bo.csv"
PARAMS = ROOT / "catalog" / "tham-so-gia.json"
# Cột nội bộ: không bao giờ đưa ra landing page / feed quảng cáo
COSTS = ROOT / "catalog" / "gia-cost.csv"          # NỘI BỘ, đã .gitignore
COSTS_SAMPLE = ROOT / "catalog" / "gia-cost.mau.csv"  # mẫu dùng khi chưa có file thật
PRIVATE = {"gia_cost_nha_may", "kich_thuoc_kien_cm", "nhom_cbpg", "_gia"}

BRAND = "Lia Casa"
LOAI_GIA = {"co_san", "cap_nhat_sau"}
REQUIRED = ["sku", "ten", "danh_muc", "xuat_xu", "loai_gia", "anh", "ngay_cap_nhat"]


def to_int(value: str) -> int | None:
    value = (value or "").replace(".", "").replace(",", "").replace(" ", "").strip()
    return int(value) if value.isdigit() else None


def the_tich_m3(kich_thuoc: str) -> float | None:
    """'72x85x80' (cm) -> m³."""
    parts = [p for p in kich_thuoc.lower().replace("*", "x").replace("×", "x").split("x") if p.strip()]
    try:
        d, r, c = (float(p.strip().replace(",", ".")) for p in parts)
    except ValueError:
        return None
    return d * r * c / 1_000_000


def tinh_gia(cost: int, kich_thuoc: str, nhom: str, p: dict) -> dict | None:
    """Giá vốn cập bến & giá bán đề xuất cho 1 đơn vị. None nếu thiếu dữ liệu."""
    m3 = the_tich_m3(kich_thuoc)
    if not cost or m3 is None:
        return None
    van_chuyen = m3 * p["van_chuyen_vnd_m3"]
    uy_thac = cost * p["phi_uy_thac"]
    gia_tinh_thue = cost + van_chuyen
    thue_nk = gia_tinh_thue * p["thue_nhap_khau"]
    cbpg = gia_tinh_thue * p["cbpg_du_phong"].get(nhom or "khong", 0.0)
    vat = (gia_tinh_thue + thue_nk + cbpg) * p["vat_nhap_khau"]
    gia_von = cost + van_chuyen + uy_thac + thue_nk + cbpg + vat
    mau = 1 - p["bien_lai_muc_tieu"] - p["chi_phi_ban_hang"]
    if mau <= 0:
        raise SystemExit("tham-so-gia.json: bien_lai_muc_tieu + chi_phi_ban_hang phải < 100%")
    step = p["lam_tron_den"]
    gia_ban = -(-gia_von / mau // step) * step  # làm tròn lên
    return {"the_tich_m3": round(m3, 4), "gia_von_cap_ben": round(gia_von), "gia_ban_de_xuat": int(gia_ban)}


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


def merge_costs(rows: list[dict]) -> str | None:
    """Gộp cost nội bộ (gia-cost.csv, hoặc file mẫu) vào từng SKU."""
    src = COSTS if COSTS.exists() else COSTS_SAMPLE
    if not src.exists():
        return None
    with src.open(encoding="utf-8-sig", newline="") as f:
        costs = {r["sku"].strip(): r for r in csv.DictReader(f) if r.get("sku")}
    for r in rows:
        c = costs.get(r["sku"], {})
        r["gia_cost_nha_may"] = to_int(c.get("gia_cost_nha_may", ""))
        r["kich_thuoc_kien_cm"] = (c.get("kich_thuoc_kien_cm") or "").strip()
        r["nhom_cbpg"] = (c.get("nhom_cbpg") or "khong").strip()
    return src.name


def write_json(rows: list[dict]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "thuong_hieu": BRAND,
        "cap_nhat": max((r["ngay_cap_nhat"] for r in rows), default=""),
        "san_pham": [{k: v for k, v in r.items() if k not in PRIVATE} for r in rows],
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
                "image_link": r["anh"] if r["anh"].startswith("http") else f"{base_url.rstrip('/')}/{r['anh']}",
                "brand": BRAND,
                "product_type": r["danh_muc"],
            })
            count += 1
    return count


def write_costs(rows: list[dict], params: dict) -> list[str]:
    """Tính giá vốn/giá đề xuất; trả về cảnh báo bán dưới hệ số tối thiểu."""
    warns = []
    cols = ["sku", "ten", "loai_gia", "gia_cost_nha_may", "the_tich_m3", "gia_von_cap_ben",
            "gia_ban_de_xuat", "gia_dang_ban", "he_so_gia_ban_tren_von"]
    with OUT_COST.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            g = tinh_gia(r.get("gia_cost_nha_may"), r.get("kich_thuoc_kien_cm", ""), r.get("nhom_cbpg", ""), params)
            r["_gia"] = g
            if not g:
                continue
            dang_ban = r["gia_khuyen_mai"] or r["gia_niem_yet"]
            he_so = round(dang_ban / g["gia_von_cap_ben"], 2) if dang_ban else ""
            if he_so and he_so < params["canh_bao_he_so_toi_thieu"]:
                warns.append(f"{r['sku']}: giá bán chỉ = {he_so}× giá vốn cập bến "
                             f"(tối thiểu {params['canh_bao_he_so_toi_thieu']}×) – kiểm tra lại giá/KM")
            w.writerow({**r, **g, "gia_dang_ban": dang_ban or "", "he_so_gia_ban_tren_von": he_so})
    return warns


def write_quote_list(rows: list[dict]) -> int:
    cols = ["sku", "ten", "danh_muc", "xuat_xu", "gia_du_kien_tu", "gia_ban_de_xuat", "thoi_gian_giao", "ngay_cap_nhat"]
    items = [{**r, "gia_ban_de_xuat": (r.get("_gia") or {}).get("gia_ban_de_xuat", "")}
             for r in rows if r["loai_gia"] == "cap_nhat_sau"]
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
    params = json.loads(PARAMS.read_text(encoding="utf-8"))
    cost_src = merge_costs(rows)
    errors += write_costs(rows, params)
    write_json(rows)
    n_feed = write_feed(rows, args.base_url)
    n_quote = write_quote_list(rows)

    print(f"✔ {len(rows)} sản phẩm hợp lệ -> {OUT_JSON.relative_to(ROOT)}")
    print(f"✔ {n_feed} SKU giá sẵn -> {OUT_FEED.relative_to(ROOT)}")
    print(f"✔ {n_quote} SKU giá cập nhật sau -> {OUT_QUOTE.relative_to(ROOT)}")
    print(f"✔ giá vốn & giá đề xuất (nội bộ, nguồn {cost_src}) -> {OUT_COST.relative_to(ROOT)}")
    for e in errors:
        print(f"⚠ {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
