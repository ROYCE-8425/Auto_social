---
type: wiki
status: active
tags: [wiki]
origin: javis-learned
created: 2026-09-09
updated: 2026-09-09
source: [[conversations/2026-09-09]]
---
Khi đăng Fanpage bằng Facebook Graph API, nếu hệ thống có Page Access Token riêng cho Page ID thì nên resolve và dùng token đó trước khi gọi `me/accounts` qua OAuth app chung [[conversations/2026-09-09]].

Cách này giúp page đã có token riêng không bị phụ thuộc vào connection OAuth cũ, đặc biệt khi app OAuth cũ đã bị Meta báo đã xóa hoặc không hợp lệ [[conversations/2026-09-09]].

Phạm vi an toàn chỉ áp dụng cho những page đã có Page Token riêng hợp lệ; page chưa có token riêng vẫn có thể rơi về luồng OAuth cũ nếu hệ thống còn fallback [[conversations/2026-09-09]].
