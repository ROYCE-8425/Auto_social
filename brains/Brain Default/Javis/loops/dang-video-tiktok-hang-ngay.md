---
type: loop
name: Đăng video TikTok hàng ngày
slug: dang-video-tiktok-hang-ngay
enabled: false
mode: full
goal: custom
interval_min: 60
quiet_hours: 22-07
max_runs_per_day: 5
notify: false
updated: 2026-09-17
---

Mỗi ngày CHỈ đăng tối đa 1 bài TikTok (carousel ảnh 9:16 hoặc video), rồi DỪNG. Cấm spam nhiều bài trong ngày. Cấm gọi các tool fb_page_*.

## Bảo vệ server & Quota PostPeer:
- Giới hạn 1 bài/ngày để tiết kiệm credit PostPeer (1 credit/post).
- Khi script điều phối báo `NEXT=NONE`, dừng ngay lập tức mà không gọi thêm lệnh hay LLM.
- Ưu tiên đăng Carousel 4–6 ảnh dọc 9:16 qua `postpeer_tiktok_photos` (auto gắn nhạc) từ nguồn `attachments/dataset/_xuat-tiktok/<brand>/` hoặc dataset.

## Quy trình 1 vòng:
1. Chạy lệnh điều phối:
   - Trên VPS: `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py`
   - Trên Local: `python "brains/Brain Default/skills/dang-video-tiktok/scripts/pick_next_tiktok.py"`
2. Xử lý kết quả:
   - Nếu output trả `NEXT=NONE <lý_do>`:
     Báo cáo đúng 1 dòng: `NEXT=NONE <lý_do>` và DỪNG NGAY VÒNG.
   - Nếu output trả `NEXT=1`:
     Lấy các tham số `account_id`, `video_url`, `the`, `hotline`, `username`, `kit`.
3. Soạn caption và đăng bài:
   - Viết caption ngắn gọn (8-18 dòng) theo đúng quy chuẩn `skills/dang-carousel-tiktok/SKILL.md` hoặc `skills/dang-video-tiktok/SKILL.md`.
   - Đăng Carousel Ảnh 9:16 (Khuyên dùng):
     Gọi tool `postpeer_tiktok_photos`:
     `postpeer_tiktok_photos(account_id="<account_id>", images=["https://trannhuy.online/tiktok-media/<brand>/<anh1>", ...], caption="<caption_ngan>", auto_add_music=true, disable_duet=true, disable_stitch=true)`
   - Hoặc Đăng Video dọc (nếu có video CDN):
     Gọi tool `postpeer_tiktok_post`:
     `postpeer_tiktok_post(account_id="<account_id>", video="<video_url>", caption="<caption_ngan>")`
4. Kết thúc vòng:
   - Nếu thành công:
     Chạy lệnh ghi nhận: `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py --ok "<url_hoac_id>"`
     Báo cáo: `TIKTOK_POST_OK post_id=<postpeer_id> link=<tiktok_url>`
   - Nếu lỗi:
     Chạy lệnh ghi nhận lỗi: `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py --fail "<url_hoac_id>" "<lý_do>"`
     Báo cáo: `TIKTOK_POST_FAIL error=<lý_do>`
