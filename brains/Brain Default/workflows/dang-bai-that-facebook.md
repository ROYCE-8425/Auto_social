---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: "Đăng bài Fanpage Facebook: Album 6-8 ảnh chuẩn Tỷ Lệ Vàng 2026 (1 cover AI mới 100% bằng GPT Image 2 + ảnh lớp học thật từ dataset), đăng bằng fb_page_album."
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Quy trình 2 bước đăng ALBUM Tỷ Lệ Vàng 2026 (6-8 ảnh): (1) BẮT BUỘC chọn 1 trong 5 khóa học chuẩn của Sao Việt (tin-hoc _ai, do-hoa, ke-toan, ve-ky-thuat, tre-em), đọc file wiki/courses/<khoa_hoc>.md lấy Tiêu đề & Highlights chuẩn. CẤM tự bịa khóa học ngoài dataset (CẤM kinh doanh online, CẤM bán hàng). Gọi tool javis_generate_image (GPT Image 2) với save_under='attachments/dataset/_xuat', ai_render_brand=true, prompt yêu cầu bố cục chữ và logo nằm trọn trong vùng an toàn cách đều 4 mép 15-20% (tuyệt đối không để chữ sát mép hay bị cắt mất chữ) tạo 1 ảnh bìa độc quyền mới 100% đúng khóa học đó. (2) Soạn caption 7 nhịp theo giáo trình wiki/courses kèm chân trang brand kit, gọi fb_page_album(page=..., photos='auto', course='<khoa_hoc>', cover='<ảnh_AI>', message=...) để đăng Album Facebook chuẩn 6, 7 hoặc 8 ảnh vuông 1:1."
updated: 2026-09-08
---
1 goal = 1 Fanpage = 1 brief. Album 6-8 ảnh chuẩn Tỷ Lệ Vàng Facebook 2026 (1 cover AI mới 100% + 5-7 ảnh lớp học thật) đăng bằng fb_page_album.
