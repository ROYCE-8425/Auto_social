---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: Đăng bài Fanpage Facebook: Mỗi bài 1 ảnh AI tạo mới 100% độc quyền (GPT Image / Imagen 3), đăng bằng fb_page_photo.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Quy trình chuẩn 2 bước: (1) Gọi tool gen ảnh AI (javis_generate_image dùng GPT Image hoặc gemini_generate_image dùng Imagen 3) với save_under='attachments/dataset/_xuat' để tạo 1 ảnh độc quyền mới 100% đúng chủ đề khóa học. CẤM dùng template cứng nhắc, CẤM bịa học phí. (2) Soạn caption chuẩn 7 nhịp kèm chân trang brand kit, gọi fb_page_photo(page=..., photo=..., message=...) để đăng bài lên Facebook. CẤM ghép album hay bốc ảnh dataset cũ."
updated: 2026-09-08
---
1 goal = 1 Fanpage = 1 brief. Đúng 1 ảnh do AI (Imagen 3 / GPT Image) sáng tạo mới tinh 100% đăng bằng fb_page_photo.
