---
name: Đăng TikTok carousel
description: "Đăng carousel 4-6 ảnh dọc 9:16 lên TikTok qua PostPeer: Tự động gắn nhạc nền gợi ý (autoAddMusic), caption 8-18 dòng đúng brand kit (BSN @seotrum vs Tin học Sao Việt)."
group: TikTok
---

# Đăng TikTok Carousel - Chuẩn 4-6 Ảnh Dọc 9:16 & Auto Nhạc

Mục tiêu: Đăng **carousel 4–6 ảnh dọc (9:16)** lên kênh TikTok thương hiệu qua PostPeer API bằng tool `postpeer_tiktok_photos`. Tự động gắn nhạc nền gợi ý của TikTok (`auto_add_music: true`), caption ngắn gọn 8–18 dòng đúng Brand Kit, tối ưu tương tác và chuyển đổi.

## Quy ước đường dẫn & kết nối:
- Script điều phối hàng đợi (nếu dùng loop): `skills/dang-video-tiktok/scripts/pick_next_tiktok.py`
- Brand Kit: `wiki/brand-kits/<kit>.md` (lấy `accountId`, `username`, `hashtags`, `disable_duet`, `disable_stitch`)
- Thư mục ảnh xuất bản: `attachments/dataset/_xuat-tiktok/<brand>/`
- Public Media URL: `https://trannhuy.online/tiktok-media/<brand>/<file_name>`
- Nhật ký bài đăng: `Javis/tiktok-posts.jsonl`

---

## Luồng thực hiện chuẩn 4 bước:

### 1. Phân định thương hiệu từ Brand Kit (CẤM lẫn lộn)
- **Nếu là Game Giá Rẻ BSN** (`game-gia-re-bsn.md`):
  * Kênh TikTok: `@seotrum` (accountId: `6aa3ba9df4c58f3c57921507`)
  * Sản phẩm: Chọn 1 tựa game Steam hot từ `wiki/courses/game-bsn.md` và dataset `attachments/dataset/game-bsn/<slug>/` (ví dụ: The Blood of Dawnwalker, STAR WARS: Zero Company, Halloween: The Game, Bus Simulator 27...).
  * Hashtag chuẩn: `#GameGiaReBSN #SteamOffline #GameBanQuyen #KeyGameGiaRe #VietHoa`
  * **TUYỆT ĐỐI CẤM**: Mang văn mẫu đào tạo, tin học văn phòng hay 13 cơ sở của Sao Việt vào kênh Game BSN.
- **Nếu là Tin Học Sao Việt**:
  * Kênh TikTok: Tin Học Sao Việt (đọc khối `## Kênh TikTok` trong kit)
  * Chủ đề: Mẹo Excel, thủ thuật Word/AI, phím tắt thực chiến.
  * Hashtag chuẩn: `#TinhocSaoViet #MeoExcel #HocExcel #ExcelOnline #ThuthuatVanphong`
  * **TUYỆT ĐỐI CẤM**: Dùng nội dung game hay học phí ngoài tài liệu chính thức.

### 2. Chuẩn bị 4–6 ảnh dọc 9:16 (Public HTTPS URL)
- Chọn 4–6 ảnh dọc sắc nét từ dataset `attachments/dataset/game-bsn/<slug>/` hoặc trong thư mục `attachments/dataset/_xuat-tiktok/<brand>/`.
- Tùy chọn tạo Cover AI dọc 9:16 bằng `javis_generate_image`:
  `javis_generate_image(prompt="Poster game/chủ đề...", aspect_ratio="portrait", save_under="attachments/dataset/_xuat-tiktok/<brand>", ai_render_brand=true)`
- **Chuyển thành Public HTTPS URLs**:
  PostPeer chỉ nhận URL công khai qua giao thức HTTPS. Sử dụng đường dẫn phục vụ media:
  `https://trannhuy.online/tiktok-media/<brand>/<file_name>`
  *(Ví dụ: `https://trannhuy.online/tiktok-media/bsn/the-blood-of-dawnwalker-01.jpg`)*

### 3. Soạn caption chuẩn TikTok (8–18 dòng)
- **Dòng 1 (Hook giật tít)**: Câu mở đầu in hoa gây tò mò, đánh trúng sở thích game thủ / nỗi đau công việc:
  * Ví dụ BSN: `SIÊU PHẨM DARK FANTASY CHẶT CHÉM ĐÃ CÓ BẢN VIỆT HÓA CỰC ĐỈNH! 🔥`
  * Ví dụ Sao Việt: `BẬT TÍNH NĂNG NÀY TRONG EXCEL ĐỂ TIẾT KIỆM 2 TIẾNG MỖI NGÀY! 🔥`
- **Dòng 2–6 (Nội dung cốt lõi)**: 3 điểm lôi cuốn nhất / 3 bước thực hiện ngắn gọn:
  * Điểm 1 / Bước 1: ...
  * Điểm 2 / Bước 2: ...
  * Điểm 3 / Bước 3: ...
- **Dòng 7–10 (CTA ngắn gọn)**:
  * Thả tim và lưu clip để chơi dần / áp dụng khi cần.
  * Hướng dẫn inbox Fanpage hoặc link bio để nhận game / tài liệu.
- **Dòng cuối (Hashtag)**: Tối đa 3–5 hashtag chuẩn từ Brand Kit.

### 4. Đăng bài qua PostPeer API (`postpeer_tiktok_photos`)
Gọi tool native:
```text
postpeer_tiktok_photos(
  account_id="<account_id>",
  images=[
    "https://trannhuy.online/tiktok-media/<brand>/anh_01.jpg",
    "https://trannhuy.online/tiktok-media/<brand>/anh_02.jpg",
    "https://trannhuy.online/tiktok-media/<brand>/anh_03.jpg",
    "https://trannhuy.online/tiktok-media/<brand>/anh_04.jpg"
  ],
  caption="<caption_8_den_18_dong>",
  auto_add_music=true,
  disable_duet=true,
  disable_stitch=true
)
```

Khi tool trả kết quả thành công:
- Ghi log vào `Javis/tiktok-posts.jsonl`.
- Báo cáo kết quả đúng 1 dòng:
  `TIKTOK_POST_OK post_id=<id> link=<tiktok_url> | <Brand> | Carousel <N> ảnh 9:16 + Auto Nhạc`

---

## Các điều cấm tuyệt đối:
1. **CẤM mock post_id**: post_id bắt buộc là ID thật do PostPeer API trả về.
2. **CẤM truyền đường dẫn file local**: Tham số `images` bắt buộc là danh sách URL `https://...` công khai.
3. **CẤM gọi các tool Facebook (`fb_*`)**: Đây là kênh TikTok, không dùng tool Fanpage.
4. **CẤM ghi lộ API Key PostPeer**: Không bao giờ đưa raw secret vào file markdown hay log.
5. **CẤM dán chân trang 13 cơ sở của Sao Việt**: TikTok yêu cầu súc tích, ngắn gọn 8–18 dòng.
