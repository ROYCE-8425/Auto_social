---
name: "Đánh giá report model trước deploy"
description: "Đối chiếu report của model khác với code local, test và rủi ro trước khi đưa thay đổi lên VPS."
group: "AI"
origin: javis-learned
status: active
created: 2026-09-08
---
## Khi nào dùng

Dùng khi người dùng gửi report từ Gemini, Claude, Codex hoặc model khác và hỏi có nên tin, có nên deploy, hoặc cần test gì trước khi đưa lên VPS.

Dùng cho các tình huống report nói đã sửa code, đã test pass, đã commit/push, hoặc đã tối ưu một workflow nhưng cần kiểm chứng bằng local thật.

## Chuẩn bị

- Đọc file/report người dùng đính kèm.
- Đọc file đang mở nếu dashboard cung cấp block file đang mở.
- Xác định các claim cụ thể trong report: file đã sửa, function mới, CLI mới, test đã chạy, commit/push, hành vi runtime.
- Kiểm tra `Javis/index.md` nếu report liên quan agent, workflow, skill hoặc loop.

## Cách chạy

- Chỉ tin claim khi thấy bằng chứng trong workspace hoặc log/test thật.
- Ưu tiên `rg` để tìm symbol, function, option CLI, test name và commit hash.
- Nếu workspace không phải git repo hoặc thiếu remote, nói rõ phần không xác minh được.
- Nếu có thể chạy test local, chạy đúng test liên quan trước, sau đó mới mở rộng.
- Nếu cần model khác test, chỉ nói có thể khi tool/CLI tương ứng thật sự có trong môi trường.

## Quy trình

1. Tách report thành danh sách claim kiểm chứng được.
2. Tìm từng claim trong code local bằng `rg` hoặc đọc file trực tiếp.
3. Đối chiếu agent, workflow, skill, plugin và script nếu report nói đã đổi luồng.
4. Kiểm tra test được nhắc trong report có tồn tại không.
5. Nếu test tồn tại, chạy test hẹp trước.
6. Nếu report nói đã commit/push, kiểm `git status`, `git log`, `git remote` khi repo cho phép.
7. Kết luận theo 3 mức: khớp code local, đúng thiết kế nhưng chưa thấy code, hoặc sai/không đủ bằng chứng.
8. Đề xuất bước trước deploy: test luồng chính, test lỗi path/fallback, test verify, đo thời gian và token.

## Bẫy

- Không nhận report là thật chỉ vì nó ghi `tests passed`.
- Không nói có thể gọi Gemini text nếu môi trường chỉ có tool tạo ảnh Gemini.
- Không nhầm plan kiến trúc với code đã tồn tại.
- Không deploy khi chưa có bằng chứng test xanh hoặc khi local không khớp report.
- Không tạo task nền chỉ vì mình đề xuất bước test, trừ khi người dùng yêu cầu giao chạy nền.

## Kiểm chứng

- Có bảng hoặc danh sách claim trong report và trạng thái local tương ứng.
- Có nêu rõ file/function nào thấy hoặc không thấy.
- Có nêu rõ test nào đã chạy, pass/fail, hoặc lý do chưa chạy được.
- Có kết luận deploy/no-deploy dựa trên bằng chứng, không dựa trên niềm tin vào report.
