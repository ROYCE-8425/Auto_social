---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: "Đăng bài Fanpage Facebook: Mỗi bài 1 ảnh AI tạo mới 100% độc quyền bằng GPT Image 2 (javis_generate_image), đăng bằng fb_page_photo."
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Quy trình 2 bước dựa 100% dataset khóa học: (1) BẮT BUỘC chọn 1 trong 5 khóa học chuẩn của Sao Việt (tin-hoc _ai, do-hoa, ke-toan, ve-ky-thuat, tre-em), đọc file wiki/courses/<khoa_hoc>.md lấy Tiêu đề & Highlights chuẩn. CẤM tự bịa khóa học ngoài dataset (CẤM kinh doanh online, CẤM bán hàng). Gọi tool javis_generate_image (GPT Image 2) với save_under='attachments/dataset/_xuat', ai_render_brand=true tạo 1 ảnh độc quyền mới 100% đúng khóa học đó. (2) Soạn caption 7 nhịp bám sát giáo trình trong wiki/courses kèm chân trang brand kit, gọi fb_page_photo(page=..., photo=..., message=...) để đăng bài lên Facebook. CẤM ghép album, CẤM bốc ảnh cũ."
updated: 2026-09-08
---
1 goal = 1 Fanpage = 1 brief. Đúng 1 ảnh tạo mới 100% bằng GPT Image 2 (javis_generate_image) đăng bằng fb_page_photo.
