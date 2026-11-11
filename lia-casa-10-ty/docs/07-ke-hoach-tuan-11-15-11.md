# 07 · Kế hoạch tuần 11/11 – 15/11/2026: hoàn thiện 4 hạng mục trước Chủ nhật

Mục tiêu tới **Chủ nhật 15/11**: (1) video quảng cáo tự dựng + tự đăng + tự chạy ads, (2) chatbot tự trả lời Facebook & Zalo, (3) catalogue PDF, (4) website chọn sản phẩm – tất cả chạy bằng **dữ liệu thật** của Lia Casa.

## Trạng thái hiện tại (đã làm xong phần kỹ thuật, đang chạy với dữ liệu MẪU)

| # | Hạng mục | Công cụ | Trạng thái |
|---|---|---|---|
| 1 | Video quảng cáo 9:16 tự dựng + caption | `tools/make_videos.py` | ✅ Chạy được – cần ảnh & giá thật |
| 1 | Tự đăng Fanpage + tự tạo QC nhắn tin + tự tắt QC kém | `tools/dang_bai_ads.py` | ✅ Chạy thử OK – cần quyền Meta |
| 2 | Chatbot Messenger / Instagram / Zalo OA | `chatbot/server.py`, `chatbot/engine.py` | ✅ 9 kịch bản kiểm thử đạt – cần token + máy chủ |
| 3 | Catalogue PDF (bản có giá / không giá) | `tools/make_catalogue.py` | ✅ Chạy được – cần dữ liệu thật |
| 4 | Website chọn sản phẩm: tìm kiếm, lọc, **danh sách chọn**, tạm tính, gửi báo giá / Zalo | `landing/index.html` | ✅ Chạy được – cần tên miền |

**Một lệnh cập nhật mọi thứ khi đổi sản phẩm/giá:**
```bash
python3 tools/build_catalog.py && python3 tools/make_catalogue.py && python3 tools/make_videos.py --top 8
```

## ⚠️ Lia Casa cần cung cấp (càng sớm càng tốt – hạn chót trong ngoặc)

| Việc | Ai | Hạn |
|---|---|---|
| Danh sách **20–30 sản phẩm chủ lực**: tên, danh mục, xuất xứ, chất liệu, kích thước, **giá sẵn** hoặc **giá cập nhật sau** (+ "dự kiến từ") – điền theo `catalog/catalog.csv` | Kinh doanh | **T5 12/11 trưa** |
| **Ảnh thật** mỗi sản phẩm (vuông ≥1080px, nền sạch/phối cảnh) đặt tên `<SKU>.jpg` | Marketing | **T5 12/11** |
| Giá cost nhà máy + kích thước kiện → `catalog/gia-cost.csv` (nội bộ) | Mua hàng | T5 12/11 |
| Hotline, Zalo, địa chỉ showroom, chính sách bảo hành/giao hàng thật | Chủ DN | T5 12/11 |
| Quyền **Admin Fanpage** + **Business Manager** + **Tài khoản quảng cáo** (thêm người phụ trách kỹ thuật) | Chủ DN | **T5 12/11** |
| **Zalo Official Account** (đã xác thực) + quyền quản trị | Chủ DN | T5 12/11 |
| Tên miền (VD liacasa.vn) + nơi đặt chatbot (Render/Railway ~5 USD/tháng hoặc VPS) | Chủ DN | T6 13/11 |
| Ngân sách test: **500.000 – 700.000đ/ngày** (≈ 14–20 tr/tháng theo kế hoạch) + thẻ thanh toán trên TK QC | Chủ DN | T7 14/11 |
| Nhạc nền có bản quyền (tuỳ chọn) → `video/nhac-nen.mp3` | Marketing | T6 13/11 |

## Lịch từng ngày

### Thứ 4 – 11/11 (hôm nay) ✅
- [x] Dựng xong 4 công cụ (video/đăng/ads, chatbot, catalogue, web chọn SP) – chạy với dữ liệu mẫu.
- [ ] Lia Casa: gom danh sách SP + ảnh, cấp quyền Page/BM/TK QC, Zalo OA.

### Thứ 5 – 12/11: Dữ liệu thật + tài khoản
- Nhập 20–30 SP thật vào `catalog/catalog.csv`, ảnh vào `landing/anh/` → chạy lệnh cập nhật → **web + catalogue PDF bản 1**.
- Duyệt catalogue PDF (chính tả, giá, ảnh) → chỉnh → **bản chốt gửi khách qua Zalo**.
- Tạo **Meta App** (loại Business) gắn BM; tạo **System User** → token quyền `pages_messaging`, `pages_manage_posts`, `pages_read_engagement`, `ads_management`, `instagram_manage_messages`.
- Tạo **ứng dụng Zalo** (developers.zalo.me), liên kết OA, lấy access/refresh token, OA Secret Key.

### Thứ 6 – 13/11: Video + chatbot lên sóng
- Chạy `make_videos.py --top 8` → duyệt 8 video tự động; quay thêm 2–4 video người thật tại showroom (kịch bản `docs/02`).
- Đưa web lên tên miền (Netlify/Vercel kéo thả thư mục `landing/`), điền Pixel Meta/TikTok, Zalo, hotline trong `window.LIA`.
- Triển khai chatbot lên máy chủ (xem *Phụ lục A*), kết nối webhook Facebook + Instagram + Zalo.
- **Test chatbot 20 câu hỏi thật** (hỏi giá, hỏi ghế/sofa, gõ SĐT, gặp nhân viên, Zalo gõ số) trên điện thoại.

### Thứ 7 – 14/11: Tự đăng + tự chạy ads
- `dang_bai_ads.py dang --lich "..." --that` → hẹn đăng **2 video/ngày** (11:30 & 20:00) cho 4 ngày tới.
- `dang_bai_ads.py ads --ngan-sach 150000 --that` → tạo chiến dịch *Nhắn tin* (TẠM DỪNG) → kiểm tra trong Ads Manager → **bật**.
- TikTok: đăng 1–2 video/ngày (Metricool hẹn lịch hoặc đăng tay), chọn video tốt nhất chạy Spark Ads.
- Hướng dẫn sale: nhận lead từ `chatbot/data/leads.csv` / Google Sheet, gọi trong 15 phút, cập nhật trạng thái.

### Chủ nhật – 15/11: Nghiệm thu
- Chạy `dang_bai_ads.py toi-uu` (chạy thử) → xem CPL từng video.
- Kiểm tra checklist nghiệm thu bên dưới, ghi lại lỗi → sửa → **bàn giao**.
- Lên lịch tuần sau: 2 video mới/tuần, cập nhật giá mỗi thứ 2, chạy `toi-uu` mỗi sáng.

## Checklist nghiệm thu Chủ nhật

- [ ] Web mở trên điện thoại < 3 giây, đủ SP thật, chọn nhiều SP → tạm tính đúng → gửi báo giá về Sheet/Zalo.
- [ ] Catalogue PDF bản có giá & không giá – đúng giá, đủ ảnh, đúng liên hệ.
- [ ] ≥ 8 video đã dựng, ≥ 4 video đã đăng/hẹn đăng trên Fanpage, caption có link + hotline.
- [ ] Chiến dịch QC Nhắn tin **đang chạy**, Pixel ghi nhận `Lead` khi gửi form.
- [ ] Nhắn Fanpage, Instagram, Zalo OA → bot trả lời < 10 giây, báo đúng giá, xin SĐT, lưu lead.
- [ ] "Gặp nhân viên" → bot dừng, sale nhận được thông báo.
- [ ] Sale biết quy trình nhận & gọi lead.

---

## Phụ lục A – Triển khai chatbot

1. **Máy chủ** (chọn 1): Render / Railway (dùng `chatbot/Dockerfile`), hoặc VPS: `pip install requests && python3 -m chatbot.server` (chạy trong thư mục `lia-casa-10-ty`, sau Nginx + HTTPS).
2. **Biến môi trường** (đặt trên máy chủ, không ghi vào repo): `FB_VERIFY_TOKEN`, `FB_APP_SECRET`, `FB_PAGE_TOKEN`, `ZALO_APP_ID`, `ZALO_APP_SECRET`, `ZALO_OA_SECRET`, `ZALO_ACCESS_TOKEN`, `ZALO_REFRESH_TOKEN`, `LEAD_WEBHOOK` (Google Sheet), `NOTIFY_WEBHOOK` (báo lead nóng).
3. **Facebook/Instagram**: Meta App → *Messenger* → Webhooks → Callback URL `https://<máy-chủ>/webhook/facebook`, Verify token = `FB_VERIFY_TOKEN` → đăng ký trường `messages`, `messaging_postbacks` cho Page (và Instagram).
4. **Zalo OA**: developers.zalo.me → ứng dụng → *Webhook* → URL `https://<máy-chủ>/webhook/zalo` → bật sự kiện `user_send_text`.
5. Kiểm tra: mở `https://<máy-chủ>/health` → `ok`; nhắn thử "giá sofa" vào Page và OA.
6. Bot im lặng khi khách bấm "Gặp nhân viên" – sale trả lời trực tiếp trong Inbox / Zalo OA.

## Phụ lục B – Lưu ý quảng cáo tự động

- Công cụ tạo QC ở trạng thái **TẠM DỪNG** mặc định – luôn xem lại trong Ads Manager lần đầu.
- `toi-uu` chỉ **tạm dừng** QC kém (chi ≥ 300k mà CPL > 250k hoặc 0 tin nhắn), không tự tăng ngân sách. Tăng ngân sách do người quyết theo `docs/04`.
- Meta có thể yêu cầu xác minh doanh nghiệp / quyền nâng cao (Advanced Access) cho App trước khi gọi API thật – làm từ T5.
- Chỉ dùng nhạc có bản quyền; ảnh/video sản phẩm thật, không dùng ảnh mẫu khi chạy QC.
