---
type: wiki
status: active
tags: [wiki]
origin: javis-learned
created: 2026-09-08
updated: 2026-09-08
source: [[conversations/2026-09-08]]
---
Deterministic-First là cách chuyển các bước có luật rõ ràng như chọn file, chuẩn hóa album, resolve path và kiểm chứng API sang code deterministic, để model chỉ xử lý phần cần suy luận hoặc viết nội dung. [[conversations/2026-09-08]]

Trong workflow đăng bài Facebook, nguồn đính kèm đề xuất dùng Python để chọn sẵn 5-8 ảnh và chuẩn hóa payload album, nhờ đó số vòng model mục tiêu giảm từ 34 turns xuống còn 2-3 turns. [[conversations/2026-09-08]]

Dự báo trong nguồn là mức tiêu hao giảm từ khoảng 2.780.000 token xuống 120.000-150.000 token cho một bài sau tối ưu Deterministic-First, nhưng đây là mục tiêu/kế hoạch cần kiểm chứng bằng usage-events sau triển khai. [[conversations/2026-09-08]]

Nguyên tắc áp dụng là: để model viết caption hoặc ra quyết định ngôn ngữ, còn các thao tác lặp lại như dò file, sửa đường dẫn, tạo payload, gọi API và verify kết quả nên được đóng gói thành script hoặc plugin. [[conversations/2026-09-08]]
