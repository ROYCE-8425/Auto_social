---
name: Đăng bài Facebook
description: "Đăng bài Fanpage Sao Việt: Mỗi bài 1 ảnh AI tạo mới 100%, đăng bằng fb_page_photo kèm caption 7 nhịp brand kit."
group: Facebook
---

# Đăng bài Facebook - 1 Bài = 1 Ảnh AI Tạo Mới 100%

Mục tiêu: Mỗi bài đăng Fanpage có đúng **1 ảnh độc quyền do GPT Image 2 (`javis_generate_image`) tạo mới 100%**, đăng nhanh bằng `fb_page_photo` kèm caption 7 nhịp chuẩn brand kit. Không ghép album, không dùng ảnh cũ từ dataset.

## Luồng thực hiện chuẩn 2 bước:

### Bước 1: BẮT BUỘC tạo 1 ảnh AI mới 100% bằng GPT Image 2
- GỌI THẲNG TOOL DUY NHẤT: `javis_generate_image` (CẤM phân vân chọn model khác để tránh tốn token và thời gian suy nghĩ):
  ```text
  javis_generate_image(
    prompt="Banner tuyển sinh thực chiến khóa học <tên_khóa_học> Sao Việt, phong cách thiết kế hiện đại, không gian học tập công nghệ, màu sắc thương hiệu xanh dương và cam, ánh sáng chuyên nghiệp, độ nét cao",
    save_under="attachments/dataset/_xuat",
    ai_render_brand=true
  )
  ```
- Lấy đường dẫn file AI trả về: `res["rel_path"]` (dạng `attachments/dataset/_xuat/cover_...png`).
- Nếu tạo ảnh thất bại: dừng ngay với `POST_SKIP ly-do=thieu-cover-ai`. **TUYỆT ĐỐI CẤM lấy ảnh cũ thay thế.**

### Bước 2: Soạn Caption & Đăng Bài bằng `fb_page_photo`
1. **Xác định Fanpage & Brand Kit**: Đọc đúng 1 file `wiki/brand-kits/<kit-page>.md` (ví dụ `royce-shop.md`). Lấy Page ID, hotline, địa chỉ và chân trang CHAN_TRANG.
2. **Sáng tạo Caption (Luồng 7 nhịp Sao Việt)**:
   - Bài thường: 32-45 dòng. Bài tuyển sinh/ads: 45-70 dòng (chưa tính chân trang).
   - Nhịp điệu: Móc câu -> Nỗi đau (`👉`) -> Giải pháp/thành quả (`✅`) -> Quyền lợi (`📌`) -> Ưu đãi/quà tặng (`🎁`) -> CTA (`📩`/`📞`) -> Chân trang CHAN_TRANG.
   - Không Markdown `**`, không em dash, không mở đầu bằng "Chiến dịch tuyển sinh", CẤM bịa học phí.
3. **Đăng Bài (Đúng 1 ảnh AI vừa tạo)**:
   - **Tool function (Khuyến nghị)**:
     ```text
     fb_page_photo(
       page="<tên_page_hoặc_page_id>",
       photo="<đường_dẫn_ảnh_AI_ở_bước_1>",
       message="<nội_dung_caption_đầy_đủ>"
     )
     ```
   - **Hoặc CLI**:
     ```text
     python "brains/Brain Default/scratch/hub_call.py" fb fb_page_photo '{"page": "<tên_page>", "photo": "<đường_dẫn_ảnh_AI>", "message": "<nội_dung_caption>"}'
     ```
4. **Báo cáo ngắn gọn 1 dòng**:
   `OK | <Trang> | <Khóa học> | 1 ảnh AI mới | post_id: <post_id> | link: <link>`

## Quy định nghiêm ngặt:
- TUYỆT ĐỐI CẤM dùng ảnh cũ trong `_xuat` hoặc ảnh lớp học trong `dataset`.
- CẤM tự chạy vòng lặp ReAct dò tìm file ảnh hay crop ảnh.
- CẤM gọi subagent kiểm chứng độc lập (verifier) vì Graph API đã tự động verify kết quả.
- CẤM dán nguyên văn caption dài hay nhật ký suy luận vào kết quả cuối.
- CẤM bịa post_id hoặc dừng ở bản nháp hỏi lại.
