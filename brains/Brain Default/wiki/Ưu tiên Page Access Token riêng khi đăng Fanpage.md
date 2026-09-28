---
type: wiki
status: active
tags: [wiki]
origin: javis-learned
created: 2026-09-09
updated: 2026-09-09
source: [[conversations/2026-09-09]]
---
Khi một workflow đăng Fanpage có `page_tokens.json`, bước resolve page nên kiểm tra Page ID trong token thủ công trước khi gọi OAuth `me/accounts`, vì OAuth connection cũ có thể trỏ tới app đã bị xóa và làm hỏng cả luồng đăng. [[conversations/2026-09-09]]

Nếu Page ID có Page Access Token riêng, plugin nên dùng token đó cho toàn bộ bước upload ảnh và đăng album, đồng thời không fallback sang OAuth app cũ trong cùng request. [[conversations/2026-09-09]]

Cách kiểm chứng tối thiểu là test hàm resolve trả đúng `pid`, `name`, độ dài token hợp lệ và `err: None`; kiểm chứng mạnh hơn là chạy goal thật và xác nhận có `post_id`. [[conversations/2026-09-09]]
