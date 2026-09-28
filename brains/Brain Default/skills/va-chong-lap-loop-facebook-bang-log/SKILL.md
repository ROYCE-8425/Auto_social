---
name: "Vá chống lặp loop Facebook bằng log"
description: "Vá picker loop Facebook để không chọn lại page đã có POST_OK trong log hôm nay."
group: "Facebook"
origin: javis-learned
status: active
created: 2026-09-11
---
## Khi nào dùng

Dùng khi loop đăng bài Facebook bị đăng lặp page trong cùng ngày, hoặc khi `Javis/dang-hang-ngay.json` không khớp với `Javis/loop-log/YYYY-MM-DD.md`.

Dấu hiệu thường gặp:

- Log có nhiều `POST_OK` hơn số page duy nhất.
- State còn `pending` dù log đã có bài cho page đó.
- Picker tiếp tục chọn page đã đăng hôm nay.
- Có nghi ngờ state bị reset hoặc ghi thiếu giữa buổi.

## Chuẩn bị

Đọc các file liên quan trước khi sửa:

- Workflow đang mở nếu user có block `FILE ĐANG MỞ`.
- `Javis/dang-hang-ngay.json` để xem `ok`, `pending_course`, `skip`, `done_day`, `sleep_until`.
- `Javis/loop-log/YYYY-MM-DD.md` để đếm `POST_OK` trong ngày.
- `skills/dang-bai-facebook/scripts/pick_next_fanpage.py` để tìm logic chọn page.
- `.claude/skills/dang-bai-facebook/scripts/pick_next_fanpage.py` nếu worker có thể dùng mirror.

## Cách chạy

1. Đếm tổng dòng `POST_OK` trong log hôm nay.
2. Rút page id từ `post_id` hoặc metadata của từng dòng `POST_OK`.
3. So sánh số page duy nhất trong log với `ok` trong state.
4. Nếu log đã có page nhưng state chưa có, coi state là thiếu.
5. Sửa picker để trước khi chọn page, nó đọc log hôm nay và merge page đã `POST_OK status=verified` vào `ok`.
6. Nếu sau khi merge đã đủ page, picker phải trả `NEXT=NONE`.
7. Đồng bộ bản sửa sang mirror `.claude/skills` nếu mirror tồn tại.
8. Kiểm cú pháp Python.
9. Chạy picker một lần ở trạng thái hiện tại để xác nhận không chọn thêm page đã đăng.

## Quy trình

Ưu tiên vá ở lớp picker, vì đây là chốt cuối trước khi sinh bài mới. Không chỉ sửa state hiện tại, vì state có thể tiếp tục bị ghi thiếu sau này.

Logic cần có:

- Xác định ngày chạy hiện tại.
- Mở `Javis/loop-log/<ngày>.md`.
- Lọc các dòng có `POST_OK` và `status=verified`.
- Rút page id đã đăng trong ngày.
- Hợp nhất danh sách này vào `ok` của state trước khi tính pending.
- Không xóa dữ liệu cũ nếu không cần.
- Nếu tất cả page đã có trong `ok` sau khi merge, set hoặc trả trạng thái hết hàng trong ngày.

Khi file script bị root-owned và không ghi trực tiếp được, kiểm quyền trước. Nếu thư mục cho phép ghi, có thể thay file bằng bản mới qua ghi tạm rồi replace để tránh kẹt quyền ở lần sau.

## Bẫy

- Đếm `ok` trong state là chưa đủ nếu state từng reset.
- Đếm tổng bài `POST_OK` cũng chưa đủ, vì một page có thể có nhiều bài.
- Không được kết luận loop đang chạy tiếp chỉ vì còn session Codex sống; phải đối chiếu mốc log mới nhất.
- Nếu chỉ sửa bản trong `skills/` mà worker đọc mirror `.claude/skills/`, lỗi có thể tái diễn.
- Không dùng các dòng summary có chữ `NEXT=NONE` làm bằng chứng duy nhất cho trạng thái thật.

## Kiểm chứng

Sau khi sửa, cần xác nhận:

- `python -m py_compile` với script picker không lỗi.
- Hàm đọc log nhận ra đúng số page đã đăng trong ngày.
- Chạy picker khi log đã phủ đủ page phải trả `NEXT=NONE`.
- `pending_course` không giữ khóa học cũ sau khi đã hết page.
- State không tạo thêm page pending đã có `POST_OK` trong log hôm nay.
