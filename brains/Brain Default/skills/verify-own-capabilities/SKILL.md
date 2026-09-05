---
name: "Kiểm tra lại năng lực của chính mình"
description: "Khi không chắc về một năng lực (vd: tạo ảnh), hãy kiểm tra danh sách tool/plugin đang hoạt động thay vì khẳng định là không có."
group: "AI"
origin: javis-learned
status: active
created: 2026-09-05
---
## Khi nào dùng
Khi người dùng hỏi về một khả năng mà bạn nghĩ mình không có, đặc biệt là các tính năng được mô tả trong system prompt như tạo ảnh, đọc web, gọi API, v.v.

## Quy trình
1.  **Dừng lại:** Không vội vàng trả lời "tôi không thể" hoặc "tôi chưa được trang bị".
2.  **Tự kiểm tra:** Dùng tool `javis_search_tools` với từ khoá liên quan đến khả năng được hỏi (ví dụ: "tạo ảnh", "generate image", "sinh ảnh").
3.  **Trả lời dựa trên bằng chứng:**
    - Nếu tool tồn tại, hãy xác nhận với người dùng rằng bạn có khả năng đó và mô tả cách dùng (tên tool, tham số cần thiết).
    - Nếu không tìm thấy tool, lúc đó mới trả lời rằng engine hiện tại chưa được trang bị công cụ đó, hoặc người dùng cần kết nối MCP/plugin tương ứng.

## Bẫy
- System prompt liệt kê các năng lực chung của Javis, nhưng việc chúng có hoạt động hay không phụ thuộc vào model đang chạy và các plugin/MCP được người dùng kết nối.
- Câu trả lời "tôi không thể" của model Gemini trong hội thoại gốc là một sai lầm vì nó đã không kiểm tra danh sách tool của chính mình trước khi trả lời, dẫn đến việc cung cấp thông tin sai cho người dùng. [[conversations/2026-09-05]]
