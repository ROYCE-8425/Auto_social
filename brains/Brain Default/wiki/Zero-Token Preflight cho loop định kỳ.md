---
type: wiki
status: active
tags: [wiki]
origin: javis-learned
created: 2026-09-09
updated: 2026-09-09
source: [[conversations/2026-09-09]]
---
Zero-Token Preflight là cơ chế chạy một kiểm tra rẻ bằng code trước khi mở phiên LLM cho loop định kỳ, để quyết định có thật sự cần spawn model hay không [[conversations/2026-09-09]].

Với loop đăng bài Facebook, preflight chạy `pick_next_fanpage.py`; nếu kết quả là `NEXT=NONE`, scheduler ghi `done_day` và `sleep_until`, rồi return trước khi mở phiên model [[van-ban-dan-135124]].

Cơ chế này biến trạng thái hết việc trong ngày từ polling tốn khoảng 60k token mỗi 5 phút thành một lần kiểm tra Python tốn 0 token LLM cho các tick tiếp theo (thực tế tính đến 09/09/2026 theo báo cáo và kiểm tra runtime) [[conversations/2026-09-09]].

Điều kiện an toàn là preflight phải dùng output máy rõ ràng như `NEXT=NONE`, không dựa vào câu tóm tắt tự nhiên của agent, vì agent từng claim sai rằng toàn bộ Fanpage đã đủ bài trong khi chỉ một page cụ thể đã đủ [[conversations/2026-09-09]].
