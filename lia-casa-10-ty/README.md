# LIA CASA – Kế hoạch 10 tỷ doanh thu qua Facebook · Instagram · TikTok

Bộ tài liệu & công cụ triển khai cho **Lia Casa – Nội thất nhập khẩu**.

| # | Hạng mục | File |
|---|----------|------|
| 0 | Chiến lược tổng & bóc tách mục tiêu 10 tỷ | [docs/00-chien-luoc-tong.md](docs/00-chien-luoc-tong.md) |
| 1 | Catalog: giá sẵn & giá cập nhật sau | [docs/01-catalog.md](docs/01-catalog.md) · [catalog/catalog.csv](catalog/catalog.csv) |
| 2 | Video quảng cáo (kịch bản + lịch sản xuất) | [docs/02-video-quang-cao.md](docs/02-video-quang-cao.md) |
| 3 | Landing page | [docs/03-landing-page.md](docs/03-landing-page.md) · [landing/index.html](landing/index.html) |
| 4 | Tối ưu kênh truyền thông FB / IG / TikTok | [docs/04-toi-uu-kenh.md](docs/04-toi-uu-kenh.md) |
| 5 | Chatbot (Messenger / Instagram / TikTok / Zalo) | [docs/05-chatbot.md](docs/05-chatbot.md) · [chatbot/kich-ban.json](chatbot/kich-ban.json) |
| 6 | Lộ trình 12 tháng, nhân sự, KPI | [docs/06-lo-trinh-kpi.md](docs/06-lo-trinh-kpi.md) |
| 7 | **Kế hoạch tuần 11–15/11**: hoàn thiện video/ads, chatbot, catalogue, web | [docs/07-ke-hoach-tuan-11-15-11.md](docs/07-ke-hoach-tuan-11-15-11.md) |

## Công cụ

| Việc | Lệnh |
|---|---|
| Cập nhật catalog → web + feed QC | `python3 tools/build_catalog.py` |
| Catalogue PDF (có giá / không giá) | `python3 tools/make_catalogue.py` → `catalogue/` |
| Dựng video QC 9:16 + caption | `python3 tools/make_videos.py --top 8` → `video/out/` |
| Tự đăng Fanpage / tạo QC / tự tắt QC kém | `python3 tools/dang_bai_ads.py dang` · `ads` · `toi-uu` (thêm `--that` để chạy thật) |
| Chatbot FB + IG + Zalo | `python3 -m chatbot.server` (xem docs/07 Phụ lục A) |
| Kiểm thử chatbot | `python3 -m unittest chatbot.test_engine` |
| Ảnh mẫu cho SKU chưa có ảnh | `python3 tools/tao_anh_mau.py` |

## Quy trình cập nhật catalog (1 lệnh)

```bash
# 1. Sửa giá / thêm sản phẩm trong catalog/catalog.csv
# 2. Sinh lại dữ liệu cho landing page + feed quảng cáo Meta/TikTok
python3 tools/build_catalog.py
```

Kết quả:
- `landing/catalog.json` → landing page tự hiển thị giá mới.
- `catalog/feed-meta-tiktok.csv` → upload lên Meta Commerce Manager & TikTok Catalog (chỉ gồm sản phẩm **đã có giá**).
- `catalog/bao-gia-cho-cap-nhat.csv` → danh sách sản phẩm **giá cập nhật sau** (kèm giá đề xuất) để sale chủ động báo giá.
- `catalog/gia-von-noi-bo.csv` → giá vốn cập bến & giá đề xuất tính từ cost nhà máy (**nội bộ, không commit**).

Giá cost nhập vào `catalog/gia-cost.csv` (đã `.gitignore`). Tham số thuế/cước/biên lãi: `catalog/tham-so-gia.json`.

## Xem landing page trên máy

```bash
python3 tools/build_catalog.py
cd landing && python3 -m http.server 8000   # mở http://localhost:8000
```

> ⚠️ Toàn bộ sản phẩm, giá, số liệu trong bộ này là **dữ liệu mẫu / giả định** để dựng khung.
> Thay bằng dữ liệu thật của Lia Casa trước khi chạy quảng cáo.
