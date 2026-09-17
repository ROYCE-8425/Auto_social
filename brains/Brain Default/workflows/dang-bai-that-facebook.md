---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: "Đăng bài Fanpage Facebook: Album 6-8 ảnh chuẩn Tỷ Lệ Vàng 2026 (1 cover AI mới 100% bằng GPT Image 2 + ảnh lớp học thật từ dataset), đăng bằng fb_page_album."
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Quy trình 2 bước đăng ALBUM Tỷ Lệ Vàng 2026 (6-8 ảnh): (1) Nếu Brief dành cho Fanpage Game Giá Rẻ BSN (Page ID 343562028848465 / slug game-gia-re-bsn / bán game): BẮT BUỘC chọn 1 tựa game hot từ wiki/courses/game-bsn.md (và attachments/dataset/game-bsn/<game-slug>/), gọi javis_generate_image tạo cover AI Gaming Dark/Cyberpunk mới 100%. Nếu Brief dành cho hệ thống Tin Học Sao Việt: BẮT BUỘC chọn 1 trong 5 khóa học chuẩn (tin-hoc _ai, do-hoa, ke-toan, ve-ky-thuat, tre-em) trong wiki/courses/, tạo cover AI giáo dục chuẩn nhận diện. CẤM tự bịa ngành ngoài dataset. (2) Soạn caption thực chiến (BSN dùng công thức Gaming AIDA Trụ cột 5 trong skills/viet-bai-facebook, Sao Việt dùng 4 Content Pillars), kèm chân trang chuẩn của ĐÚNG Fanpage đó (BSN không có địa chỉ). Gọi fb_page_album(page='<page_được_yêu_cầu>', photos='auto', course='<khoa_hoc_hoac_game>', cover='<ảnh_AI>', message=...). TUYỆT ĐỐI CẤM tự ý đổi sang Page khác nếu page được yêu cầu lỗi token, phải báo lỗi dừng bằng POST_SKIP."
updated: 2026-09-17
---
1 goal = 1 Fanpage = 1 brief. Album 6-8 ảnh chuẩn Tỷ Lệ Vàng Facebook 2026 (1 cover AI mới 100% + 5-7 ảnh lớp học thật) đăng bằng fb_page_album.
