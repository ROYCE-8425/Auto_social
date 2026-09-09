---
name: "Kiểm tra loop đăng bài Facebook"
description: "Kiểm tra loop đăng bài Facebook: trạng thái, lần chạy, treo ở đâu, token, post_id, ảnh và lỗi lặp page."
group: "Facebook"
origin: javis-learned
status: active
created: 2026-09-09
---
## Khi nào dùng

Dùng khi người dùng hỏi một việc định kỳ đăng Facebook đang chạy thế nào, có bị treo không, vì sao token tăng, hoặc loop có đăng sai/lặp page không.

Ví dụ trigger:
- "kiểm tra việc định kỳ này đi"
- "tiến trình đang chạy dính cái gì vậy mà đang treo"
- "loop đăng Facebook hôm nay chạy chưa"
- "xem nó có đăng lặp page không"

## Chuẩn bị

- Đọc file loop trong `Javis/loops/` theo slug người dùng đưa.
- Đọc state chính của loop, thường là `Javis/dang-hang-ngay.json` hoặc file state được ghi trong loop.
- Đọc `Javis/loop-state.json` để lấy `last_run`, `runs_today`, `post_id`, trạng thái gần nhất.
- Đọc log đúng ngày trong `Javis/loop-log*` hoặc log liên quan nếu có.
- Nếu có session đang chạy, kiểm tiến trình shell/Codex liên quan và lệnh con đang sống.

## Cách chạy

1. Xác định đúng slug loop và file loop.
2. Kiểm frontmatter hoặc cấu hình: `enabled`, `mode`, chu kỳ, `owner_chat`, page/page_id.
3. Đối chiếu với state hôm nay: `ok`, `failed`, `pending_course`, `page_last_course`, `runs_today`.
4. Tìm lần chạy gần nhất trong loop-state, Kanban, session log và artifact ảnh.
5. Nếu người dùng hỏi "treo", kiểm tiến trình đang chạy trước khi kết luận.
6. Nếu có `post_id`, kiểm payload đăng album, số ảnh, khóa học và trạng thái verify.
7. Ghép usage token theo session hoặc thời điểm chạy gần nhất.

## Quy trình

- Phân biệt rõ 3 trạng thái: chưa chạy, đang chạy, đã chạy nhưng UI/state chưa cập nhật.
- Nếu thấy `hub_call.py run fb_page_album`, kiểm xem nó còn sống hay đã trả `post_id`.
- Nếu token tăng, tìm nguyên nhân theo thứ tự: retry tạo cover AI, fallback hub, đọc code/log quá nhiều, verifier lặp, lỗi quyền file state.
- Với loop 1 Fanpage, luôn test nhánh `pick_next_fanpage.py --page <page_id>` để xem page đã nằm trong `ok` có bị chặn không.
- Nếu script mặc định chạy trước rồi mới gọi `--page`, đánh dấu là luồng chưa sạch vì có thể tạo token thừa hoặc state rác.
- Khi kiểm ảnh, không chỉ nhìn thư mục output sau chạy vì có thể còn ảnh cũ. Cần xác nhận payload thật gửi lên Facebook dùng những file nào.

## Bẫy

- Đừng kết luận loop đang chạy chỉ vì `enabled: true`; phải có `last_run`, log hoặc tiến trình thật.
- Đừng kết luận treo chết khi lệnh upload Facebook còn đang chạy; cần chờ đủ bằng chứng hoặc kiểm tiến trình.
- Đừng dùng ảnh còn sót trong `album_ready` làm bằng chứng album đã đăng.
- Đừng bỏ qua `owner_chat` trống, vì kết quả có thể không quay về đúng chat người hỏi.
- Đừng gọi công cụ ghi hoặc bật/tắt loop nếu người dùng chỉ yêu cầu kiểm tra.

## Kiểm chứng

Báo cáo cuối cần có:
- Loop đang bật hay tắt.
- Lần chạy gần nhất và số lần chạy hôm nay.
- Nếu đang treo: treo ở lệnh/bước nào.
- Nếu đã đăng: `post_id`, số ảnh, khóa học, verify.
- Token/thời gian nếu ghép được.
- Một đến ba lỗi hoặc hành động sửa cụ thể tiếp theo.
