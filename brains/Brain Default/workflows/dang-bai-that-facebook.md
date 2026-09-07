---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: Đăng bài Fanpage Facebook kèm album khóa học chuẩn Sao Việt với cover AI tạo mới độc quyền.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Quy trình chuẩn 2 bước: (1) Gọi tool gen ảnh AI (javis_generate_image dùng GPT Image hoặc gemini_generate_image dùng Imagen 3) với save_under='attachments/dataset/_xuat' để tạo 1 cover độc quyền mới 100% đúng chủ đề khóa học. CẤM dùng template cứng nhắc hay bịa học phí. (2) Soạn caption chuẩn 7 nhịp kèm chân trang brand kit, gọi fb_page_album(page=..., course=..., cover=..., photos='auto', message=...) để ghép cover AI vừa tạo với album dataset và đăng lên Facebook. CẤM ReAct dò file hay crop ảnh thủ công."
updated: 2026-09-08
---
1 goal = 1 Fanpage = 1 brief. Cover do AI (Imagen 3 / GPT Image) sáng tạo mới tinh + album ảnh thật dataset.
