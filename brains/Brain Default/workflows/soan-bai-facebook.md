---
type: workflow
name: Soạn bài Facebook
slug: soan-bai-facebook
status: on
description: Kanban soạn caption Fanpage theo brand kit. Chỉ nháp, không tự đăng.
steps:
  - agent: bien-tap-facebook
    task: "Brief = {{input}}. CHỈ NHÁP, cấm tool đăng. Đọc: wiki/brand-kits/_index.md → _mac-dinh.md → wiki/brand-kits/<slug>.md. Ảnh gợi ý (không đăng): attachments/dataset/<folder>/. Thiếu slug/tên Fanpage trong brief → [[NEEDS_INPUT]]. Ghi sources/facebook-nhap/<slug>/YYYY-MM-DD.md."
updated: 2026-09-03
---
Dùng trên trang Việc: Route = Workflow Soạn bài Facebook. Bật **AI tự vận hành**. Tick **Yêu cầu duyệt kết quả**. Không tự đăng.
