---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: Co anh dataset thi mac dinh cover va album dung anh that. Neu brief ghi OpenAI/GPT Image/javis_generate_image/ai_render_brand=true/ai_full thi cho AI render poster full.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. FAST_PATH: đọc đúng 1 brand-kits/<page> theo brief (royce=royce-shop.md, page_id 988656934325292) và skills/dang-bai-facebook/SKILL.md; không đọc corpus/reference dài trừ khi user yêu cầu. Nếu brief có OpenAI/GPT Image/gpt-image/javis_generate_image/ai_render_brand=true/ai_full/AI tự render logo tiêu đề hotline thì cover BẮT BUỘC gọi trực tiếp javis_generate_image với ai_render_brand=true, page_id, save_under='attachments/dataset/_xuat'; prompt ảnh phải đúng ngành, brand hiển thị luôn Tin Học Sao Việt/Trung Tâm Tin Học Sao Việt, tên page như Royce Shop chỉ là nơi đăng không render thành badge/logo, cấm template code/overlay/split-panel/card cũ. Bài khóa học phải đi kèm album ảnh thật dataset đúng ngành: dùng pick_photos để tạo tổng 5-8 ảnh nếu đủ ảnh, photos[0]=cover AI. Caption tự nhiên 32-45 dòng hoặc 45-70 nếu ads đầy đủ, có emoji dẫn mắt vừa đủ, chân trang đúng kit. Đăng thật bằng fb_page_album khi có album; chỉ fb_page_photo nếu không đủ ảnh dataset. Lấy post_id thật. Cấm hỏi duyệt, cấm bịa link/post_id, cấm fb_page_post."
updated: 2026-09-05
---
1 goal = 1 Fanpage = 1 brief. Chân trang pháp nhân đầy đủ.
