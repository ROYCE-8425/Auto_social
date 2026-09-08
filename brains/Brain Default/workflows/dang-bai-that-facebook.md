---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: Đăng bài Fanpage Facebook: Mỗi bài 1 ảnh AI tạo mới 100% độc quyền bằng GPT Image 2 (javis_generate_image), đăng bằng fb_page_photo.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Quy trình chuẩn 2 bước: (1) BẮT BUỘC gọi thẳng tool javis_generate_image (GPT Image 2) với save_under='attachments/dataset/_xuat', ai_render_brand=true để tạo 1 ảnh độc quyền mới 100% đúng chủ đề khóa học. CẤM đắn đo chọn model khác, CẤM dùng template cứng nhắc, CẤM bịa học phí. (2) Soạn caption chuẩn 7 nhịp kèm chân trang brand kit, gọi fb_page_photo(page=..., photo=..., message=...) để đăng bài lên Facebook. CẤM ghép album hay bốc ảnh dataset cũ."
updated: 2026-09-08
---
1 goal = 1 Fanpage = 1 brief. Đúng 1 ảnh tạo mới 100% bằng GPT Image 2 (javis_generate_image) đăng bằng fb_page_photo.
