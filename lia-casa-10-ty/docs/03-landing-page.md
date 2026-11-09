# 03 · Landing page

File: [`landing/index.html`](../landing/index.html) – 1 file tĩnh, đọc dữ liệu từ `landing/catalog.json` (sinh bởi `tools/build_catalog.py`).

## 1. Cấu trúc trang (theo thứ tự chuyển đổi)

1. **Hero** – lời hứa chính + 2 nút: *Xem catalog* / *Tư vấn miễn phí*.
2. **USP** – Chính hãng CO/CQ · Bảo hành 5 năm · Giao lắp miễn phí · Thiết kế 3D miễn phí.
3. **Catalog có bộ lọc** – tự hiển thị:
   - Giá sẵn → giá niêm yết, giá KM gạch ngang, nút *Giữ hàng ngay*.
   - Giá cập nhật sau → "Giá cập nhật sau · Dự kiến từ X đ · Báo giá trong 15 phút", nút *Nhận báo giá*.
4. **Quy trình 4 bước** – giảm lo ngại khi mua hàng giá trị lớn.
5. **Form báo giá** – Họ tên, SĐT/Zalo, sản phẩm, ngân sách, ghi chú.
6. **Nút nổi** Zalo · Messenger · Gọi.

## 2. Cấu hình trước khi chạy

Sửa khối `window.LIA` ở đầu `index.html`:

| Biến | Ý nghĩa |
|---|---|
| `META_PIXEL_ID` | Pixel Meta (FB + IG). Sự kiện: `PageView`, `ViewContent`, `Lead`, `Contact` |
| `TIKTOK_PIXEL_ID` | Pixel TikTok. Sự kiện: `page`, `ViewContent`, `SubmitForm`, `Contact` |
| `LEAD_WEBHOOK` | URL nhận lead (Google Apps Script bên dưới hoặc CRM). Để trống → mở Zalo sau khi gửi |
| `ZALO_PHONE`, `MESSENGER_PAGE`, `HOTLINE` | Kênh liên hệ |

Landing tự ghi nhận `utm_source`, `utm_campaign`… → biết lead đến từ kênh/chiến dịch nào.
Quy ước link quảng cáo: `?utm_source=facebook|instagram|tiktok&utm_campaign=<ten>&utm_content=<ma_video>`.

## 3. Nhận lead về Google Sheet (miễn phí)

1. Tạo Google Sheet, hàng 1: `thoi_gian | ho_ten | sdt | san_pham | ngan_sach | ghi_chu | nguon | utm`.
2. *Tiện ích mở rộng → Apps Script*, dán:

```javascript
function doPost(e) {
  const d = JSON.parse(e.postData.contents);
  SpreadsheetApp.getActiveSheet().appendRow([
    d.thoi_gian, d.ho_ten, "'" + d.sdt, d.san_pham, d.ngan_sach, d.ghi_chu, d.nguon, JSON.stringify(d.utm)
  ]);
  return ContentService.createTextOutput("ok");
}
```

3. *Triển khai → Ứng dụng web* (Ai có quyền truy cập: Bất kỳ ai) → copy URL vào `LEAD_WEBHOOK`.
4. Bật thông báo Sheet (hoặc nối Zapier/Make → Zalo nhóm sale) để sale gọi trong 5–15 phút.

## 4. Triển khai hosting

- Miễn phí: GitHub Pages / Netlify / Vercel (kéo thả thư mục `landing/`).
- Gắn tên miền riêng (VD `liacasa.vn`), bật HTTPS, xác minh tên miền trong Meta Business Manager.
- Sau khi host, có thể đặt **lịch lấy feed tự động** trên Meta/TikTok từ URL `catalog/feed-meta-tiktok.csv`.

## 5. Tối ưu chuyển đổi (A/B test mỗi 2 tuần)

| Thành phần | Phương án A | Phương án B |
|---|---|---|
| Tiêu đề hero | "Nội thất nhập khẩu chính hãng…" | "Sofa Ý thật – từ 39,9 triệu" |
| CTA | Nhận báo giá | Nhận thiết kế 3D miễn phí |
| Ưu đãi | Tặng thảm/đèn đơn > 80tr | Giảm 5% cọc trong tuần |
| Form | 5 trường | 2 trường (Tên + SĐT) |

Mục tiêu: **tỷ lệ chuyển đổi landing ≥ 8%**, tốc độ tải < 2,5s trên 4G (nén ảnh WebP ≤ 200KB).
