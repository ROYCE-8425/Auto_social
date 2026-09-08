---
name: Đăng bài Facebook
description: "Đăng bài Fanpage Sao Việt: Album 6-8 ảnh chuẩn Tỷ Lệ Vàng 2026 (1 cover AI mới 100% + ảnh lớp học thật dataset), đăng bằng fb_page_album kèm caption 7 nhịp brand kit."
group: Facebook
---

# Đăng bài Facebook - Album 6-8 Ảnh Chuẩn Tỷ Lệ Vàng 2026

Mục tiêu: Mỗi bài đăng Fanpage là một **ALBUM chuẩn Tỷ Lệ Vàng Facebook 2026 (ngẫu nhiên 6, 7 hoặc 8 ảnh)** gồm: 1 ảnh bìa độc quyền do GPT Image 2 (`javis_generate_image`) tạo mới 100% + 5-7 ảnh chụp lớp học thật từ dataset đi kèm, đăng tự động bằng `fb_page_album` với `photos='auto'`.

## Luồng thực hiện chuẩn 2 bước:

### Bước 1: BẮT BUỘC tạo 1 ảnh bìa mới 100% bằng GPT Image 2
- Đọc file `wiki/courses/<khoa_hoc>.md` để lấy Tiêu đề (Title Hooks) và Highlights giáo trình chuẩn.
- GỌI THẲNG TOOL DUY NHẤT: `javis_generate_image`:
  ```text
  javis_generate_image(
    prompt="Banner tuyển sinh thực chiến khóa học <tên_khóa_học_chuẩn> Sao Việt, tiêu đề '<tiêu_đề>', các điểm nổi bật '<highlights>', phong cách thiết kế hiện đại, không gian học tập công nghệ, nhận diện xanh dương & cam Sao Việt, độ nét cao",
    save_under="attachments/dataset/_xuat",
    ai_render_brand=true
  )
  ```
- Lấy đường dẫn file AI trả về: `res["rel_path"]` (dạng `attachments/dataset/_xuat/cover_...png`).
- Nếu tạo ảnh thất bại: dừng ngay với `POST_SKIP ly-do=thieu-cover-ai`. **TUYỆT ĐỐI CẤM lấy ảnh cũ thay thế.**

### Bước 2: Soạn Caption & Đăng ALBUM bằng `fb_page_album`
1. **Xác định Fanpage & Brand Kit**: Đọc đúng 1 file `wiki/brand-kits/<kit-page>.md`. Lấy Page ID, hotline, địa chỉ và chân trang CHAN_TRANG.
2. **Sáng tạo Caption (Luồng 7 nhịp Sao Việt)**:
   - Bài thường: 32-45 dòng. Bài tuyển sinh/ads: 45-70 dòng (chưa tính chân trang).
   - Nhịp điệu: Móc câu -> Nỗi đau (`👉`) -> Giải pháp/thành quả (`✅`) -> Quyền lợi (`📌`) -> Ưu đãi/quà tặng (`🎁`) -> CTA (`📩`/`📞`) -> Chân trang CHAN_TRANG.
   - Không Markdown `**`, không em dash, CẤM bịa học phí, CẤM bịa khóa kinh doanh online.
3. **Đăng ALBUM (Tỷ Lệ Vàng 2026 - Random 6, 7 hoặc 8 ảnh vuông 1:1 đồng bộ)**:
   ```text
   fb_page_album(
     page="<tên_page_hoặc_page_id>",
     photos="auto",
     course="<tên_khóa_học_chuẩn>",
     cover="<đường_dẫn_ảnh_AI_ở_bước_1>",
     message="<nội_dung_caption_đầy_đủ>"
   )
   ```
   *(Cơ chế `photos="auto"` sẽ tự động ghép ảnh cover AI mới + 5-7 ảnh lớp học thật từ dataset của đúng khóa học đó, chuẩn hóa 100% sang tỷ lệ vuông 1:1 đồng bộ cho album 6, 7 hoặc 8 ảnh)*.
4. **Báo cáo ngắn gọn 1 dòng**:
   `OK | <Trang> | <Khóa học> | Album 6-8 ảnh (1 cover AI + ảnh dataset) | post_id: <post_id> | link: <link>`

## Quy định nghiêm ngặt:
- TUYỆT ĐỐI CẤM dùng cover cũ trong `_xuat`. Cover luôn luôn là ảnh AI mới tạo 100%.
- CẤM tự chạy vòng lặp ReAct dò tìm file ảnh hay crop ảnh thủ công (đã có tool tự động hóa).
- CẤM gọi subagent kiểm chứng độc lập (verifier) vì Graph API đã tự động verify kết quả.
- CẤM dán nguyên văn caption dài hay nhật ký suy luận vào kết quả cuối.
- CẤM bịa post_id hoặc dừng ở bản nháp hỏi lại.
