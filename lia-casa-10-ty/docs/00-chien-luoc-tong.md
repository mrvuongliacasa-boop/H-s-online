# 00 · Chiến lược tổng – Mục tiêu 10 tỷ

## 1. Bóc tách mục tiêu – 2 nhóm khách (cập nhật theo dữ liệu bán hàng thực tế)

Doanh số thực tế cho thấy doanh thu Lia Casa **dồn vào vài dự án lớn** (full nhà / công trình), còn lại là nhiều đơn lẻ giá trị nhỏ. Vì vậy mục tiêu 10 tỷ được chia theo 2 nhóm, mỗi nhóm một cách tìm khách:

| Nhóm | Giá trị TB | Số đơn / 12 tháng | Doanh thu | Nguồn khách chính |
|---|---|---|---|---|
| **A – Dự án** (full nhà, biệt thự, showroom, nhà hàng) | 250 tr | **24** (2/tháng) | **6,0 tỷ** | KTS/nhà thầu giới thiệu, khách cũ, FB/IG Lead Form nhắm biệt thự – căn hộ cao cấp |
| **B – Đơn lẻ / theo phòng** (sofa, bàn ăn, giường, đèn) | 35 tr | **~115** (~10/tháng) | **4,0 tỷ** | TikTok, Reels, FB Tin nhắn + catalog |
| **Tổng** | | **~139 đơn** | **~10 tỷ** | |

| Chỉ số | Nhóm A | Nhóm B |
|---|---|---|
| Tỷ lệ lead → đơn | 5% | 6% |
| Lead cần / năm | ~480 (½ từ KTS & giới thiệu, ½ từ ads) | ~1.900 |
| CPL mục tiêu | 180.000 đ | 180.000 đ |
| Ngân sách ads | ~43 tr | ~345 tr |

**Tổng ngân sách quảng cáo ≈ 390 triệu (~4% doanh thu)** – tăng dần theo kết quả, không chi trước.

### Nguyên tắc tài chính
1. **Không nhận đơn lỗ:** giá bán ≥ **1,4× giá vốn cập bến** (đã gồm vận chuyển, thuế, CBPG). Công cụ `tools/build_catalog.py` tự cảnh báo.
2. **Tính đủ chi phí bán hàng vào giá:** hoa hồng sale, chiết khấu KTS, quảng cáo, giao lắp → điền `chi_phi_ban_hang` trong `catalog/tham-so-gia.json` (đang để 0%).
3. **Vận chuyển nội địa/lắp đặt dự án** báo giá riêng hoặc cộng vào giá; không để "ăn" vào biên lãi.
4. **Ngân sách ads tự nuôi:** ads tháng sau ≤ 25% lợi nhuận gộp tháng trước cho tới khi CPL và tỷ lệ chốt ổn định.
5. **Thu tiền:** cọc ≥ 50% dự án, thu đủ trước khi giao; theo dõi công nợ hằng tuần.

**Công thức kiểm soát hằng tuần:**
`Doanh thu = Lead × Tỷ lệ chốt × AOV` → tuần nào hụt, xác định ngay hụt ở *lead*, *tỷ lệ chốt* hay *AOV*.

### Đòn bẩy tăng doanh thu không cần tăng ngân sách
1. **Kéo đơn lẻ thành đơn theo phòng / dự án**: combo phòng khách (sofa + bàn trà + thảm + đèn), tư vấn 3D miễn phí cho khách mua ≥ 2 món.
2. **Tăng tỷ lệ chốt**: phản hồi lead < 5 phút (chatbot), mời khách tới showroom / gọi video xem hàng.
3. **Chương trình đối tác KTS / nhà thầu**: chính sách chiết khấu cố định, catalog riêng cho KTS – đây là nguồn chính của nhóm A.

## 2. Phân bổ theo kênh

| Kênh | Vai trò | % doanh thu mục tiêu | % ngân sách ads |
|---|---|---|---|
| **Facebook** | Chốt đơn chính: Lead Form, Messenger, retarget catalog | 45% (4,5 tỷ) | 45% |
| **TikTok** | Tạo nhu cầu & tiếp cận rộng: video ngắn, livestream, TikTok Lead Gen | 35% (3,5 tỷ) | 35% |
| **Instagram** | Thương hiệu cao cấp, thẩm mỹ, retarget, DM | 20% (2,0 tỷ) | 20% |

> FB & IG chạy chung một Meta Ads Manager / một Pixel / một catalog → tối ưu chéo.

## 3. Phễu khách hàng

```
NHẬN BIẾT  ──►  QUAN TÂM  ──►  CÂN NHẮC  ──►  CHỐT  ──►  GIỚI THIỆU
Video TikTok/   Landing page   Chatbot báo giá  Showroom /   Ưu đãi khách cũ,
Reels, KOC      + catalog      + sale gọi lại   video call   hoa hồng KTS
```

| Tầng | Nội dung | Kênh | KPI |
|---|---|---|---|
| Nhận biết | Video "nhà đẹp", trước/sau, tour showroom | TikTok, Reels | CPM, ThruPlay, % xem 3s |
| Quan tâm | Video sản phẩm + giá, carousel catalog | FB/IG/TikTok | CTR > 1,5% |
| Cân nhắc | Landing page, chatbot, báo giá | Landing, Messenger, Zalo | CPL, tỷ lệ để SĐT |
| Chốt | Gọi lại, mời showroom, ưu đãi có hạn | Sale + Zalo | Tỷ lệ chốt ≥ 6% |
| Giới thiệu | Feedback, ảnh nhà khách, referral | Tất cả | % doanh thu khách cũ |

## 4. 5 hạng mục triển khai

1. **Catalog** – 2 loại giá: *giá sẵn* (hàng có sẵn kho) và *giá cập nhật sau* (hàng đặt nhập, phụ thuộc tỷ giá/lô hàng). → `01-catalog.md`
2. **Video quảng cáo** – 12–20 video/tháng, 5 dạng nội dung. → `02-video-quang-cao.md`
3. **Landing page** – 1 trang chốt lead, hiển thị catalog, form báo giá, gắn Pixel. → `03-landing-page.md`
4. **Tối ưu kênh** – cấu trúc tài khoản, lịch đăng, đo lường. → `04-toi-uu-kenh.md`
5. **Chatbot** – trả lời 24/7, phân loại khách, xin SĐT, chuyển sale. → `05-chatbot.md`

## 5. Rủi ro & phương án

| Rủi ro | Phương án |
|---|---|
| Tỷ giá biến động → giá hàng nhập thay đổi | Dùng cơ chế "giá cập nhật sau", báo giá có hiệu lực 7 ngày |
| CPL tăng cao | Làm mới video mỗi 2 tuần, mở rộng tệp lookalike từ khách đã mua |
| Lead ảo / không nghe máy | Chatbot xác thực nhu cầu, ưu tiên lead qua Messenger/Zalo |
| Hàng về chậm | Ghi rõ thời gian giao dự kiến trên catalog, cọc giữ giá |
| Phụ thuộc 1 kênh | Duy trì 3 kênh + tệp data khách riêng (Zalo OA, danh sách SĐT) |
