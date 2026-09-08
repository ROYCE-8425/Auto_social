---
name: Đăng bài Facebook
description: "Đăng bài Fanpage Sao Việt: Bắt buộc AI tạo cover độc quyền mới 100%, Python chuẩn bị album dataset và verify deterministic."
group: Facebook
---

# Đăng bài Facebook - AI Cover + Album Dataset (Chuẩn 2 Bước)

Mục tiêu: Đăng bài Fanpage thành công 100% với **ảnh cover AI độc quyền mới 100%** cho mỗi bài, kết hợp album ảnh thật từ dataset được Python chuẩn hóa và verify tự động.

## Luồng thực hiện chuẩn 2 bước

### Bước 1: BẮT BUỘC tạo cover AI vuông 1:1 mới tinh
- Gọi tool tạo ảnh AI `javis_generate_image` (dùng GPT Image) hoặc `gemini_generate_image` (dùng Imagen 3):
  ```text
  javis_generate_image(
    prompt="Banner tuyển sinh thực chiến khóa học <tên_khóa_học> Sao Việt, phong cách hiện đại, không gian học tập công nghệ, độ nét cao, tỷ lệ 1:1",
    save_under="attachments/dataset/_xuat",
    ai_render_brand=true
  )
  ```
- Lấy đường dẫn file AI trả về: `res["rel_path"]` (dạng `attachments/dataset/_xuat/cover_...png`).
- Nếu tạo ảnh thất bại: dừng ngay với `POST_SKIP ly-do=thieu-cover-ai`. **TUYỆT ĐỐI CẤM bốc cover cũ trong _xuat hay poster trong dataset.**

### Bước 2: Soạn Caption & Đăng Album kèm Cover AI vừa tạo
1. **Xác định Fanpage & Brand Kit**: Đọc đúng 1 file `wiki/brand-kits/<kit-page>.md` (ví dụ `royce-shop.md`). Lấy Page ID, hotline, địa chỉ và chân trang CHAN_TRANG.
2. **Sáng tạo Caption (Luồng 7 nhịp Sao Việt)**:
   - Bài thường: 32-45 dòng. Bài tuyển sinh/ads: 45-70 dòng (chưa tính chân trang).
   - Nhịp điệu: Móc câu -> Nỗi đau (`👉`) -> Giải pháp/thành quả (`✅`) -> Quyền lợi (`📌`) -> Ưu đãi/quà tặng (`🎁`) -> CTA (`📩`/`📞`) -> Chân trang CHAN_TRANG.
   - Không Markdown `**`, không em dash, không mở đầu bằng "Chiến dịch tuyển sinh", CẤM bịa học phí.
3. **Đăng Album (Kèm cover AI vừa tạo)**:
   - **Tool function (Khuyến nghị)**:
     ```text
     fb_page_album(
       page="<tên_page_hoặc_page_id>",
       course="<tên_khóa_học>",
       cover="<đường_dẫn_ảnh_AI_ở_bước_1>",
       message="<nội_dung_caption_đầy_đủ>",
       photos="auto"
     )
     ```
   - **Hoặc CLI**:
     ```text
     python "brains/Brain Default/scratch/hub_call.py" auto_post "<page>" "<khoa_hoc>" "<caption_text_hoặc_@file>" "<đường_dẫn_ảnh_AI>"
     ```
   *(Python sẽ ghép cover AI 1:1 với 4-7 ảnh phụ 3:2 từ dataset đúng ngành, upload Graph API và tự động verify)*.
4. **Báo cáo ngắn gọn 1 dòng**:
   `OK | <Trang> | <Khóa học> | <Số ảnh> ảnh | post_id: <post_id> | link: <link>`

## Quy định nghiêm ngặt:
- TUYỆT ĐỐI CẤM tự bốc cover cũ trong `_xuat` hoặc poster cũ trong dataset. Mỗi bài phải có cover AI mới tinh.
- CẤM tự chạy vòng lặp ReAct dò tìm file ảnh phụ hay crop ảnh thủ công.
- CẤM gọi subagent kiểm chứng độc lập (verifier) vì Graph API đã tự động verify kết quả.
- CẤM dán nguyên văn caption dài hay nhật ký suy luận vào kết quả cuối.
- CẤM bịa post_id hoặc dừng ở bản nháp hỏi lại.
