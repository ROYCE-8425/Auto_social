---
name: "Kiểm tra token workflow Javis"
description: "Rà soát workflow Javis để tìm nơi phình context, log, result và skill gây tốn token."
group: "AI"
origin: javis-learned
status: active
created: 2026-09-07
---
## Khi nào dùng

Dùng khi người dùng hỏi vì sao một workflow Javis tốn nhiều token, chạy lâu, hoặc nghi có loop nội bộ.

Dùng tốt nhất cho các workflow có Kanban task, agent, skill, mirror `.claude/skills`, log agent hoặc file result dài.

## Chuẩn bị

- Xác định slug workflow hoặc tên tác vụ người dùng nhắc tới.
- Đọc `Javis/index.md` để tránh nhầm capability.
- Đọc workflow, agent, skill canonical và mirror nếu có.
- Kiểm tra `Javis/kanban.json`, log agent trong `memory/agents/`, và các file reference/corpus mà skill có thể kéo vào.

## Cách chạy

- Chỉ đọc file, không sửa nếu người dùng chỉ yêu cầu kiểm tra.
- Dùng `rg --files`, `wc`, `sed`, `nl` hoặc script đọc ngắn để đo kích thước file và trường JSON.
- Ưu tiên đo theo ký tự, dòng và ước tính token, sau đó mới kết luận.

## Quy trình

1. Xác định đường chạy chính: workflow gọi agent nào, agent dùng skill nào, skill có reference nào.
2. Đo kích thước từng lớp prompt: workflow task, agent prompt, skill canonical, skill mirror, reference.
3. Đo dữ liệu đuôi dài: `Javis/kanban.json`, trường `result`, run log, archived task, memory agent.
4. Tìm trùng luật giữa workflow, agent và skill.
5. Tìm mirror skill lệch canonical, nhất là `.claude/skills/<slug>/SKILL.md`.
6. Kiểm tra các nhánh retry/fallback có thể làm agent tự thuật nhiều lần hoặc gọi tool lặp.
7. Nếu có báo cáo tối ưu từ model khác, đối chiếu bằng file thật trong workspace trước khi tin.
8. Kết luận theo nhóm: đã tối ưu thật, còn rủi ro, chưa xác minh được.

## Bẫy

- Không kết luận từ báo cáo đính kèm nếu chưa đối chiếu file thật.
- Không nhầm thời gian nằm queue với thời gian chạy workflow thật.
- Không chỉ nhìn workflow ngắn mà bỏ qua Kanban result và run log.
- Không đọc quét rộng làm output terminal phình quá lớn.
- Không sửa file trong vòng học read-only.

## Kiểm chứng

- Có số đo kích thước trước/sau nếu có dữ liệu.
- Có đường dẫn file và dòng đại diện cho từng nhận xét chính.
- Có phân biệt chi phí token tức thời với chi phí đuôi dài do context/log cũ bị nạp lại.
- Có nêu phần chưa xác minh được, ví dụ commit GitHub hoặc test không có trong workspace.
