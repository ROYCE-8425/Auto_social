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
- **Dòng 1 (Hook giật tít)**: Câu mở đầu in hoa nổi bật, đánh đúng nỗi đau hoặc tính năng đặc sắc trong video (ví dụ: `BẬT TÍNH NĂNG NÀY TRONG EXCEL ĐỂ TIẾT KIỆM 2 TIẾNG MỖI NGÀY! 🔥`).
- **Dòng 2–6 (Nội dung cốt lõi)**: 3 điểm lợi ích hoặc 3 bước thực hiện ngắn gọn, dùng gạch đầu dòng:
  * Bước 1 / Mẹo 1: ...
  * Bước 2 / Mẹo 2: ...
  * Bước 3 / Mẹo 3: ...
- **Dòng 7–10 (CTA ngắn gọn)**:
  * Kêu gọi lưu clip, thả tim hoặc bình luận nhận file thực hành.
  * Thông tin khoá học kèm 1-1 cấp tốc tại Sao Việt.
  * Hotline / Zalo tư vấn: lấy từ Brand Kit.
- **Dòng cuối (Hashtag)**: Tối đa 3–5 hashtag liên quan:
  `#TinhocSaoViet #HocExcel #MeoTinHoc #TinHocVanPhong #HocAI`

---

## Quy tắc cấm trên TikTok:
- **CẤM viết caption dài 30–70 dòng**: TikTok là nền tảng video ngắn, caption dài che hết màn hình clip và người xem sẽ lướt qua. Giữ đúng khung 8–18 dòng.
- **CẤM nhồi nhiều ngành**: Video về Excel thì chỉ nói Excel và Tin học văn phòng, tuyệt đối không nhồi AutoCAD hay MISA vào.
- **CẤM hứa hẹn phi thực tế**: Không dùng các từ "thành thạo sau 5 phút", "x5 mức lương ngay lập tức".
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
