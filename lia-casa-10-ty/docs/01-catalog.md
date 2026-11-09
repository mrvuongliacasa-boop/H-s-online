# 01 · Catalog – Giá sẵn & Giá cập nhật sau

## 1. Hai loại giá

| Loại | Khi nào dùng | Hiển thị cho khách | Quảng cáo |
|---|---|---|---|
| **`co_san` – Giá sẵn** | Hàng có sẵn kho/showroom, giá đã chốt | "45.900.000 đ" (+ giá KM nếu có) | Đưa vào feed catalog Meta/TikTok, chạy quảng cáo động |
| **`cap_nhat_sau` – Giá cập nhật sau** | Hàng đặt nhập theo lô, phụ thuộc tỷ giá, tuỳ chọn vải/da/kích thước | "Giá cập nhật sau – Nhận báo giá trong 15 phút" (+ "Dự kiến từ X đ" nếu có) | **Không** đưa vào feed (Meta/TikTok bắt buộc có giá). Dùng video + Lead Form để xin SĐT báo giá |

> Khi hàng "cập nhật sau" đã có giá chốt → đổi `loai_gia` thành `co_san`, điền `gia_niem_yet`, chạy lại `tools/build_catalog.py`. Sản phẩm tự vào feed quảng cáo.

## 2. Cấu trúc file `catalog/catalog.csv`

| Cột | Bắt buộc | Ví dụ | Ý nghĩa |
|---|---|---|---|
| `sku` | ✔ | LC-SF-001 | Mã duy nhất (dùng cho Pixel, feed) |
| `ten` | ✔ | Sofa da Ý Milano 3 chỗ | Tên hiển thị |
| `danh_muc` | ✔ | Sofa | Sofa / Bàn ăn / Giường / Bàn trà / Ghế / Đèn / Decor |
| `xuat_xu` | ✔ | Ý | Nước sản xuất |
| `chat_lieu` |  | Da bò thật, khung gỗ sồi | |
| `kich_thuoc` |  | 220 x 95 x 80 cm | |
| `loai_gia` | ✔ | co_san / cap_nhat_sau | Xem mục 1 |
| `gia_niem_yet` | khi `co_san` | 45900000 | Số nguyên, không dấu chấm |
| `gia_khuyen_mai` |  | 39900000 | Để trống nếu không KM |
| `gia_du_kien_tu` |  | 60000000 | Chỉ cho `cap_nhat_sau`, giá tham khảo "từ" |
| `ton_kho` |  | 3 | Số lượng có sẵn (0 = đặt hàng) |
| `thoi_gian_giao` |  | 3–5 ngày / 45–60 ngày | |
| `anh` | ✔ | https://… | Link ảnh vuông ≥ 1080px |
| `link` |  | https://liacasa.vn/… | Link sản phẩm/landing |
| `mo_ta` |  | … | 1–2 câu, nêu lợi ích |
| `ngay_cap_nhat` | ✔ | 2026-11-09 | Ngày cập nhật giá gần nhất |

## 3. Quy trình cập nhật giá (hằng tuần – thứ 2)

1. **Kế toán/mua hàng** cập nhật tỷ giá & giá về của lô mới → điền vào `catalog.csv`.
2. Chạy `python3 tools/build_catalog.py` → kiểm tra cảnh báo (thiếu giá, thiếu ảnh…).
3. Upload `catalog/feed-meta-tiktok.csv` lên **Meta Commerce Manager** và **TikTok Catalog** (hoặc đặt lịch tự lấy feed qua URL nếu host landing).
4. Gửi `catalog/bao-gia-cho-cap-nhat.csv` cho đội sale: gọi lại các khách đã hỏi những mẫu vừa có giá.
5. Ghi `ngay_cap_nhat`. Báo giá gửi khách luôn ghi **"hiệu lực 7 ngày"**.

## 4. Tính giá bán từ cost nhà máy (cho hàng "giá cập nhật sau")

Logic giống file Excel **LIA_BAO_GIA_COST**, tham số ở `catalog/tham-so-gia.json`:

```
Vận chuyển   = thể tích kiện (m³) × 1.200.000
Ủy thác      = cost × 1,5%
Thuế NK      = (cost + vận chuyển) × 8%
CBPG dự phòng= (cost + vận chuyển) × 35,2% (bàn) / 21,4% (ghế) / 0%
VAT NK       = (cost + vận chuyển + thuế NK + CBPG) × 8%
Giá vốn cập bến = cost + vận chuyển + ủy thác + thuế NK + CBPG + VAT
Giá bán đề xuất = Giá vốn / (1 − biên lãi 35% − chi phí bán hàng %)   (làm tròn lên 100.000)
```

- Nhập cost vào `catalog/gia-cost.csv` (cột `sku, gia_cost_nha_may, kich_thuoc_kien_cm, nhom_cbpg`; xem file mẫu `gia-cost.mau.csv`). **File này đã được .gitignore – không đẩy lên GitHub.**
- Chạy `python3 tools/build_catalog.py` → `catalog/gia-von-noi-bo.csv` (nội bộ) có giá vốn, giá đề xuất, hệ số giá bán/giá vốn; `bao-gia-cho-cap-nhat.csv` có thêm cột `gia_ban_de_xuat` cho sale.
- Cảnh báo tự động khi giá đang bán < **1,4× giá vốn cập bến**.
- Cost và giá vốn **không bao giờ** xuất ra landing page hay feed quảng cáo.
- ⚠️ Cơ sở tính thuế (cộng vận chuyển vào giá tính thuế) là cách tính phổ biến; hãy so khớp 1 dòng với file Excel trước khi dùng. CBPG chỉ là dự phòng – xác minh mã HS từng mặt hàng.

## 5. Catalog bản in / PDF gửi khách qua Zalo

- 1 trang bìa thương hiệu + 1 trang / bộ sưu tập (phòng khách, phòng ăn, phòng ngủ).
- Mỗi sản phẩm: ảnh lớn, xuất xứ, chất liệu, kích thước, **giá** hoặc **"Liên hệ – giá theo lô nhập"**, QR Zalo.
- Xuất từ Canva theo dữ liệu CSV (Bulk Create) để cập nhật nhanh khi đổi giá.

## 6. Checklist chất lượng catalog

- [ ] Ảnh nền sạch + ít nhất 1 ảnh phối cảnh trong phòng thật.
- [ ] Tên có *chất liệu + xuất xứ* (VD: "Bàn ăn đá ceramic Tây Ban Nha").
- [ ] Mọi SKU `co_san` đều có giá; mọi SKU `cap_nhat_sau` có `thoi_gian_giao`.
- [ ] Bộ sản phẩm (set) theo phòng để tăng AOV.
- [ ] Đồng bộ cùng SKU trên landing, feed, chatbot.
