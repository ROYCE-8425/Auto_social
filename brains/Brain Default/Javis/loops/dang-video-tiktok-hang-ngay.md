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

Mỗi ngày CHỈ đăng tối đa 1 video TikTok, rồi DỪNG. Cấm spam nhiều video trong ngày. Cấm gọi các tool fb_page_*.

## Bảo vệ server & Quota PostPeer:
- Giới hạn 1 video/ngày để tiết kiệm credit PostPeer (1 credit/video).
- Khi script điều phối báo `NEXT=NONE`, dừng ngay lập tức mà không gọi thêm lệnh hay LLM.

## Quy trình 1 vòng:
1. Chạy lệnh điều phối:
   - Trên VPS: `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py`
   - Trên Local: `python "brains/Brain Default/skills/dang-video-tiktok/scripts/pick_next_tiktok.py"`
2. Xử lý kết quả:
   - Nếu output trả `NEXT=NONE <lý_do>`:
     Báo cáo đúng 1 dòng: `NEXT=NONE <lý_do>` và DỪNG NGAY VÒNG.
   - Nếu output trả `NEXT=1`:
     Lấy các tham số `account_id`, `video_url`, `the`, `hotline`, `username`.
3. Soạn caption và đăng bài:
   - Viết caption ngắn gọn (8-18 dòng) theo đúng quy chuẩn `skills/dang-video-tiktok/SKILL.md`.
   - Gọi tool `postpeer_tiktok_post`:
     `postpeer_tiktok_post(account_id="<account_id>", video="<video_url>", caption="<caption_ngan>")`
4. Kết thúc vòng:
   - Nếu thành công:
     Chạy lệnh ghi nhận: `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py --ok "<video_url>"`
     Báo cáo: `TIKTOK_POST_OK post_id=<postpeer_id> link=<tiktok_url>`
   - Nếu lỗi:
     Chạy lệnh ghi nhận lỗi: `python skills/dang-video-tiktok/scripts/pick_next_tiktok.py --fail "<video_url>" "<lý_do>"`
     Báo cáo: `TIKTOK_POST_FAIL error=<lý_do>`
