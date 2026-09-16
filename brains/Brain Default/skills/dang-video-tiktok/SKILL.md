---
name: Đăng video TikTok
description: "Đăng video dọc (9:16) lên TikTok qua PostPeer: Caption ngắn 8-18 dòng, hook giật tít, 3 lợi ích nhanh, CTA ngắn gọn, tối đa 5 hashtag."
group: TikTok
---

# Đăng video TikTok - Chuẩn Ngắn Gọn 8-18 Dòng

Mục tiêu: Đăng **1 video dọc (9:16)** mỗi ngày lên kênh TikTok thương hiệu qua PostPeer. Video nguồn là URL HTTPS công khai trên CDN, caption ngắn gọn, súc tích, tối ưu tỷ lệ giữ chân và chuyển đổi.

## Quy ước đường dẫn làm việc:
- Script điều phối: `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py` (trên VPS) hoặc `python "brains/Brain Default/skills/dang-video-tiktok/scripts/pick_next_tiktok.py"` (trên Local).
- Brand Kit: `wiki/brand-kits/<kit>` (lấy `TikTok accountId`, hotline).
- Hàng đợi trạng thái: `Javis/tiktok-queue.json`.

---

## Luồng thực hiện chuẩn:

### 1. Điều phối hàng đợi:
Chạy script `pick_next_tiktok.py`:
- Nếu output trả `NEXT=NONE <lý_do>`:
  Báo cáo đúng 1 dòng máy: `NEXT=NONE <lý_do>` và **DỪNG NGAY VÒNG**. Không gọi AI, không tốn token.
- Nếu output trả `NEXT=1`:
  Nhận các tham số: `account_id`, `video_url`, `the`, `kit`, `caption_ctx`.

### 2. Viết caption chuẩn TikTok (8–18 dòng):
- Đọc thông tin từ **khối Kênh TikTok** trong Brand Kit (hashtag, username, disable_duet, caption_mode).
- **Phân biệt thương hiệu**:
  * **Sao Việt**: Mẹo tin học, thủ thuật Excel/Word/AI, khoá học thực chiến. Hashtag: `#TinhocSaoViet #HocExcel...`.
  * **Game Giá Rẻ BSN**: Giới thiệu game Steam, cốt truyện, tính năng bản quyền, bảo hành trọn đời. Hashtag: `#GameGiaRe #SteamGame...`. **TUYỆT ĐỐI CẤM** dùng mẫu caption tin học / khoá học cho BSN.
- **Dòng 1 (Hook giật tít)**: Câu mở đầu in hoa nổi bật, đánh đúng nỗi đau hoặc tính năng đặc sắc trong video (ví dụ: `BẬT TÍNH NĂNG NÀY TRONG EXCEL ĐỂ TIẾT KIỆM 2 TIẾNG MỖI NGÀY! 🔥`).
- **Dòng 2–6 (Nội dung cốt lõi)**: 3 điểm lợi ích hoặc 3 bước thực hiện ngắn gọn, dùng gạch đầu dòng:
  * Bước 1 / Điểm 1: ...
  * Bước 2 / Điểm 2: ...
  * Bước 3 / Điểm 3: ...
- **Dòng 7–10 (CTA ngắn gọn)**:
  * Kêu gọi lưu clip, thả tim hoặc bình luận nhận tài liệu / link tải.
  * Hướng dẫn xem link bio hoặc liên hệ hotline.
- **Dòng cuối (Hashtag)**: Tối đa 3–5 hashtag từ Brand Kit hoặc mặc định của brand.

---

## Quy tắc cấm trên TikTok:
- **CẤM dán chân trang Fanpage 13 cơ sở (CHAN_TRANG)**: Không bao giờ nhồi danh sách 13 chi nhánh vào clip TikTok.
- **CẤM viết caption dài 30–70 dòng**: Giữ đúng khung 8–18 dòng.
- **CẤM nhồi nhiều ngành**: Clip Excel chỉ nói Excel; clip game chỉ nói game, không nhồi chéo.
- **CẤM hứa hẹn phi thực tế**: Không dùng "thành thạo sau 5 phút", "x5 mức lương".
- **CẤM truyền đường dẫn file local**: Tool `postpeer_tiktok_post` bắt buộc URL video `https://...` công khai (CDN).

---

## Thực thi đăng bài:
Gọi tool:
```text
postpeer_tiktok_post(
  account_id="<account_id>",
  video="<video_url>",
  caption="<caption_8_den_18_dong>"
)
```

Kết thúc vòng:
- Nếu thành công: Gọi `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py --ok "<video_url>"` và báo cáo `TIKTOK_POST_OK post_id=<id> link=<tiktok_url>`.
- Nếu thất bại: Gọi `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py --fail "<video_url>" "<lý_do>"` và báo cáo `TIKTOK_POST_FAIL error=<lý_do>`.
