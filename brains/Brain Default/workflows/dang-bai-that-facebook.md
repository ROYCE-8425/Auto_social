---
type: workflow
name: Đăng Facebook
slug: dang-bai-that-facebook
status: on
description: Đăng bài Fanpage Facebook kèm album khóa học chuẩn Sao Việt.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. Soạn caption chuẩn 7 nhịp theo brand kit tương ứng. Gọi fb_page_album(page=..., course=..., message=..., photos='auto') để đăng album deterministic 1-turn. CẤM ReAct dò file hay crop ảnh thủ công."
updated: 2026-09-08
---
1 goal = 1 Fanpage = 1 brief. Chân trang pháp nhân đầy đủ.
