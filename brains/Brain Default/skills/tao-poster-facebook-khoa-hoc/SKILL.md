---
name: "Tạo poster Facebook khóa học"
description: "Tạo poster Facebook 1:1 cho khóa học bằng javis_generate_image, lưu vào vault và trả markdown ảnh."
group: "Marketing"
origin: javis-learned
status: active
created: 2026-09-07
---
## Khi nào dùng
Dùng khi người dùng yêu cầu tạo poster Facebook cho khóa học, chương trình tuyển sinh hoặc bài quảng cáo giáo dục và muốn nhận ngay ảnh trong chat.

Ví dụ trigger:
- "Tạo poster Facebook 1:1 cho khóa Tin học văn phòng & AI."
- "Dùng javis_generate_image, lưu vào attachments/dataset/_xuat, chỉ trả markdown ảnh."
- "Tạo ảnh quảng cáo khóa học, GPT tự render logo, tiêu đề, bullet và hotline."

## Chuẩn bị
Xác định rõ các tham số người dùng đã nêu:
- Công cụ tạo ảnh, ví dụ `javis_generate_image`.
- `page_id` nếu có.
- Thư mục lưu, ví dụ `attachments/dataset/_xuat`.
- Tỉ lệ ảnh, ví dụ Facebook 1:1 tương ứng `square`.
- Phong cách hình ảnh, đối tượng khóa học, nội dung bắt buộc và các kiểu layout cần tránh.

Nếu người dùng yêu cầu "chỉ trả markdown ảnh", không thêm diễn giải dài sau khi ảnh đã tạo xong.

## Cách chạy
Gọi tool tạo ảnh đang có trong Javis, ưu tiên đúng tool người dùng chỉ định.

Tham số thường dùng:
- `prompt`: viết lại đầy đủ brief ảnh, giữ nguyên các ràng buộc quan trọng.
- `aspect_ratio`: `square` cho poster Facebook 1:1.
- `quality`: chọn mức cao nếu người dùng yêu cầu poster hoàn chỉnh hoặc phong cách premium.
- `save_under`: dùng thư mục người dùng nêu nếu tool hỗ trợ.
- `page_id`: truyền đúng nếu tool hỗ trợ.
- `ai_render_brand`: bật nếu người dùng yêu cầu AI tự render logo hoặc nhận diện thương hiệu.

## Quy trình
1. Đọc kỹ brief để tách phần phải có và phần cấm.
2. Viết prompt ảnh theo hướng sản phẩm hoàn chỉnh, không mô tả chung chung.
3. Giữ các ràng buộc layout ở dạng phủ định rõ ràng, ví dụ không split-panel, không panel navy lớn, không bám template cũ.
4. Gọi `javis_generate_image` với tỉ lệ `square` khi cần poster 1:1.
5. Sau khi tool trả ảnh trong vault, trả về markdown ảnh bằng đường dẫn tương đối.
6. Nếu người dùng yêu cầu chỉ trả markdown ảnh, câu trả lời cuối chỉ có dòng ảnh.

## Bẫy
- Không tự chuyển sang tool khác nếu người dùng đã chỉ rõ `javis_generate_image`, trừ khi tool đó không callable.
- Không dùng ảnh tham chiếu hoặc template cũ khi người dùng đã cấm.
- Không viết mô tả dài nếu người dùng yêu cầu chỉ trả markdown ảnh.
- Không dùng đường dẫn tuyệt đối trong markdown ảnh, vì dashboard cần đường dẫn tương đối trong vault.

## Kiểm chứng
Kiểm tra kết quả cuối có:
- Một file ảnh đã được tạo trong thư mục người dùng yêu cầu hoặc thư mục mặc định của tool.
- Markdown ảnh dùng đường dẫn tương đối.
- Tỉ lệ đúng 1:1 nếu yêu cầu Facebook square.
- Nội dung prompt có đủ: khóa học, thương hiệu, phong cách, tiêu đề, bullet, hotline và các điều cấm.
