# 05 · Chatbot

Kịch bản dạng dữ liệu: [`chatbot/kich-ban.json`](../chatbot/kich-ban.json) – dùng để dựng trên nền tảng chatbot (VD: ManyChat cho FB/IG, Botcake/Fchat/Harasocial cho FB, Zalo OA, TikTok DM auto-reply).

## 1. Mục tiêu

| Chỉ số | Mục tiêu |
|---|---|
| Thời gian phản hồi đầu tiên | < 10 giây (24/7) |
| Tỷ lệ khách nhắn tin → để lại SĐT | ≥ 35% |
| Thời gian sale tiếp nhận lead nóng | < 5 phút (giờ hành chính), trước 9h sáng hôm sau (ngoài giờ) |

## 2. Luồng chính

```
Khách nhắn / bấm quảng cáo
        │
   [CHÀO + MENU]
   ├─ Xem catalog theo phòng ──► gửi carousel sản phẩm (từ catalog.json)
   │                               └─ bấm 1 sản phẩm ─► [HỎI GIÁ]
   ├─ Hỏi giá ───────────────────► [HỎI GIÁ]
   │        ├─ SKU giá sẵn      → báo giá + KM + tồn kho → "Giữ hàng?" → xin SĐT
   │        └─ SKU cập nhật sau → "giá theo lô nhập, dự kiến từ X" → xin SĐT báo giá chính xác
   ├─ Tư vấn thiết kế 3D ────────► hỏi diện tích, phong cách, ngân sách → xin SĐT
   ├─ Đặt lịch showroom ─────────► chọn ngày/khung giờ → xin SĐT → xác nhận
   └─ Gặp nhân viên ─────────────► chuyển sale (handoff)
        │
   [XIN SĐT] ─► kiểm tra định dạng ─► gắn tag ─► đẩy về Sheet/CRM ─► báo nhóm sale Zalo
```

## 3. Phân loại & gắn tag

| Tag | Điều kiện | Ưu tiên |
|---|---|---|
| `nong` | Đã để SĐT + ngân sách ≥ 80tr hoặc đặt lịch showroom | Gọi ngay |
| `am` | Đã để SĐT, ngân sách < 80tr | Gọi trong ngày |
| `lanh` | Chỉ xem catalog, chưa để SĐT | Retarget + tin nhắn chăm sóc sau 24h |
| `hoi_gia_cap_nhat_sau:<SKU>` | Hỏi hàng chưa có giá | Báo khi có giá (dùng `bao-gia-cho-cap-nhat.csv`) |
| `nguon:fb/ig/tiktok` | Theo kênh đến | Đo hiệu quả kênh |

## 4. Chuỗi chăm sóc tự động (khách chưa để SĐT)

| Thời điểm | Tin nhắn |
|---|---|
| +1 giờ | "Anh/chị còn phân vân mẫu nào không ạ? Em gửi thêm ảnh thực tế nhà khách nhé 📸" |
| +23 giờ | Ưu đãi tháng (trong cửa sổ 24h của Messenger) |
| Ngoài 24h | Chỉ gửi qua tin nhắn tài trợ / Zalo OA khi khách đã đồng ý nhận |

## 5. Quy tắc chuyển người thật (handoff)

Chuyển ngay cho sale khi: khách gõ "gặp nhân viên / gọi cho tôi", hỏi ngoài kịch bản 2 lần, khiếu nại/bảo hành, đơn dự án (> 200tr, nhà thầu, KTS).
Sale nhận hội thoại kèm toàn bộ tag + sản phẩm khách quan tâm.

## 6. Câu trả lời mẫu (FAQ)

Xem mục `faq` trong `kich-ban.json`: bảo hành, giao hàng, trả góp, xuất xứ/CO-CQ, đặt cọc, đổi trả, showroom ở đâu.

> Lưu ý: chatbot **không tự bịa giá** cho hàng "cập nhật sau" – luôn đọc từ catalog và chỉ nêu "dự kiến từ" nếu có.
