---
name: Soạn nháp tương tác Fanpage
description: "Soạn nháp câu trả lời comment hoặc tin nhắn khi chat trực tiếp trong /app: đúng brand kit, đúng giọng điệu, chỉ gửi thật khi người dùng xác nhận. Không thay thế Care poller."
group: Content
---

# Soạn Nháp Tương Tác Fanpage (Khi Chat /App)

Mục tiêu: Hỗ trợ người dùng trong khung chat `/app` khi muốn soạn nhanh câu trả lời cho một bình luận hoặc tin nhắn cụ thể (ví dụ khi người dùng dán `comment_id`, `thread_id` hoặc trích dẫn câu hỏi của khách).

> [!IMPORTANT]
> Skill này **chỉ phục vụ tương tác tức thời trong hội thoại chat**. Toàn bộ việc quét tự động, phân loại và sinh nháp nền 24/7 đã do **Hệ thống Care Python (`fanpage_care.py` + `/ops`)** đảm nhiệm với cơ chế zero-token preflight. **Tuyệt đối KHÔNG** biến skill này thành vòng lặp tự động hay poller thứ hai.

---

## Luồng xử lý khi người dùng yêu cầu:

### 1. Tiếp nhận ngữ cảnh từ người dùng
Người dùng gõ trong chat:
- *"Soạn câu trả lời cho comment này: ..."*
- Hoặc dán `comment_id: <id>` / `thread_id: <id>`
- Hoặc *"Khách hỏi mua game The Blood of Dawnwalker thì trả lời sao?"*

### 2. Xác định thương hiệu & đọc thông tin (Không Polling)
- Xác định Fanpage liên quan:
  * **Game Giá Rẻ BSN** (`page_id: 343562028848465`): Giọng điệu thân thiện, nhiệt tình kiểu gamer, báo giá chuẩn (game offline 28k-48k, bảo hành trọn đời, hỗ trợ cài patch Việt hóa).
  * **Tin Học Sao Việt**: Giọng điệu chuyên nghiệp, nhã nhặn, tư vấn đúng 5 khóa học chuẩn (tin học văn phòng, đồ họa, kế toán, AutoCAD, trẻ em), mời inbox tư vấn lộ trình.
- Nếu người dùng cung cấp `comment_id`: có thể gọi tool đọc một lần `fb_page_comments` để lấy ngữ cảnh bài viết và câu hỏi gốc.

### 3. Soạn nội dung phản hồi chuẩn mực
- Ngắn gọn, đúng trọng tâm, giải đáp trực tiếp thắc mắc của khách.
- Kèm lời mời tiếp theo tự nhiên (ví dụ: *"Dạ a check inbox e gửi link tải và hướng dẫn cài ngay nhé!"* hoặc *"Dạ bạn cho mình xin số điện thoại/Zalo để tư vấn lộ trình chi tiết nhé ạ"*).

### 4. Cơ chế xác nhận gửi (Human-in-the-Loop)
- **BẮT BUỘC**: Xuất trình nội dung câu trả lời nháp cho người dùng xem trước trong khung chat.
- **CHỈ GỬI THẬT** qua tool `fb_page_reply(comment_id=..., message=...)` hoặc `fb_message_send(recipient_id=..., message=...)` khi người dùng ra lệnh xác nhận rõ ràng (ví dụ: *"Gửi luôn đi"*, *"Duyệt"*, *"Đồng ý"*).
- Hoặc gợi ý người dùng truy cập `/ops/#inbox` để bấm nút duyệt gửi trên bảng CSKH chuyên dụng.

---

## Các điều cấm tuyệt đối:
1. **CẤM tự tạo vòng lặp (loop) hay cron tự động quét comment**: Care Python đã có poller chạy nền riêng.
2. **CẤM spawn worker hay gọi model định kỳ đọc comment**: Gây cạn kiệt tài nguyên VPS 4GB và lãng phí token.
3. **CẤM tự ý gửi tin nhắn/bình luận khi chưa có sự xác nhận của người dùng**.
4. **CẤM trả lời lẫn lộn giữa hai thương hiệu**: Tuyệt đối không tư vấn khóa học cho khách hỏi game BSN và ngược lại.
