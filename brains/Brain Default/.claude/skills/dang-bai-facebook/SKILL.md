---
name: Đăng bài Facebook
description: "Đăng bài Fanpage Sao Việt: Album 6-8 ảnh chuẩn Tỷ Lệ Vàng 2026 (1 cover AI mới 100% + ảnh lớp học thật dataset), đăng bằng fb_page_album kèm…"
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
    prompt="Banner tuyển sinh thực chiến khóa học <tên_khóa_học_chuẩn> Sao Việt, tiêu đề '<tiêu_đề>', các điểm nổi bật '<highlights>', bố cục chữ và logo nằm trọn trong vùng an toàn cách đều 4 mép ảnh 15-20% (tuyệt đối không để chữ sát mép hay bị cắt mất chữ), phong cách thiết kế hiện đại, không gian học tập công nghệ, nhận diện xanh dương & cam Sao Việt, độ nét cao",
    save_under="attachments/dataset/_xuat",
    ai_render_brand=true
  )
  ```
- Lấy đường dẫn file AI trả về: `res["rel_path"]` (dạng `attachments/dataset/_xuat/cover_...png`).
- **Quy tắc 1-Shot cho Cover AI**: Chỉ gọi `javis_generate_image` đúng 1 lần duy nhất. TUYỆT ĐỐI CẤM loop tạo lại ảnh nhiều lần để soi chính tả hay chữ logo (mô hình khuếch tán AI không thể render typography chính xác 100%, việc cố tạo lại sẽ đốt hàng triệu token và làm nghẽn tiến trình). Dùng trực tiếp ảnh AI sinh ra; phần logo và nhận diện đã có `ai_render_brand=true` xử lý.
- Nếu tool báo lỗi exception hoặc không sinh được file: tối đa retry 1 lần duy nhất. Nếu vẫn thất bại: dừng ngay với `POST_SKIP ly-do=thieu-cover-ai`. TUYỆT ĐỐI CẤM lấy ảnh cũ thay thế và CẤM viết script chèn logo thủ công.

### Bước 2: Soạn Caption & Đăng ALBUM bằng `fb_page_album`
1. **Xác định Fanpage & Brand Kit**: Đọc đúng 1 file `wiki/brand-kits/<kit-page>.md`. Lấy Page ID, hotline, địa chỉ và chân trang CHAN_TRANG.
2. **Sáng tạo Caption (Luồng nhịp điệu Sao Việt & Highlight chuẩn)**:
   - Bài chuẩn chuyển đổi: 32-45 dòng (chưa tính chân trang).
   - **BẮT BUỘC có highlight emoji theo từng khối** (tuyệt đối không viết toàn chữ trơn hay gạch ngang `-`):
     * Khối cam kết/điểm mạnh: 4-5 dòng, mỗi dòng bắt đầu bằng `📌` (ví dụ: `📌 Học theo nhu cầu thật, không ép học đại trà.`, `📌 Học đến khi thành thạo, không giới hạn số buổi.`, `📌 Lịch học linh hoạt sáng, chiều, tối từ Thứ 2 đến Thứ 7.`, `📌 Có thể đăng ký học ngay, không cần chờ đủ lớp.`, `📌 Phù hợp người bận rộn, người đi làm...`).
     * Khối quyền lợi/ưu đãi: 3-4 dòng, mỗi dòng bắt đầu bằng `🎁` (ví dụ: `🎁 Khi đăng ký, học viên được tư vấn lộ trình...`, `🎁 Được định hướng bộ kỹ năng cần học...`, `🎁 Được hỗ trợ giải đáp nghiệp vụ sau khóa học...`).
     * Khối kêu gọi hành động: `👉 Muốn học nhanh để dùng được ngay trong công việc?` -> `📞 Nhắn tin Fanpage hoặc gọi Hotline/Zalo để được tư vấn...` -> `📌 Nhận học viên mới mỗi tuần...`.
     * Chân trang CHAN_TRANG: BẮT BUỘC dùng đúng định dạng sạch từ `pick_next_fanpage.py` hoặc brand kit:
       - Fanpage cơ sở TP.HCM (Bình Thạnh, Quận 12, Thủ Đức, Tân Bình, Quận 7, Bình Tân/Quận 6): Chỉ hiển thị DUY NHẤT 1 địa chỉ của đúng chi nhánh đó.
       - Fanpage Bình Dương: Hiển thị ĐẦY ĐỦ cả 4 địa chỉ thuộc tỉnh Bình Dương (Dĩ An, Thuận An, Thủ Dầu Một, Tân Uyên).
       - Fanpage Đồng Nai: Hiển thị ĐẦY ĐỦ cả 2 địa chỉ thuộc tỉnh Đồng Nai (Biên Hòa, Long Thành).
       - Fanpage Vũng Tàu: Hiển thị địa chỉ cơ sở tại Vũng Tàu.
       - Fanpage tổng hệ thống / Royce Shop: Hiển thị 13 chi nhánh chuẩn.
       Mỗi cơ sở dùng icon `🏫 [Chi nhánh]: [Địa chỉ]`, `📞 Hotline/Zalo: ...`, `📧 Email: ...`, `🌐 Website: ...`. TUYỆT ĐỐI CẤM dùng chuỗi địa chỉ rác có mã bưu điện (như 700000, 75300, 75411, Di An, Ho Chi Minh City...).
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
   `POST_OK post_id=<post_id> status=verified link=https://www.facebook.com/<post_id> | <Trang> | <Khóa học> | Album 6-8 ảnh (1 cover AI + ảnh dataset)`

## Quy định nghiêm ngặt:
- Nếu `pick_next_fanpage.py` trả về `NEXT=NONE` (ví dụ `page-da-ok-hom-nay` hoặc `het-hang-hom-nay`): DỪNG NGAY TIẾN TRÌNH, không được dùng `--page` để bypass hoặc cố đăng tiếp.
- TUYỆT ĐỐI CẤM dùng cover cũ trong `_xuat`. Cover luôn luôn là ảnh AI mới tạo 100%.
- CẤM loop retry tạo cover AI vì lý do chữ nhỏ hay logo. Đúng 1 lần tạo là dùng.
- CẤM tự viết script Python (Pillow/cv2) để dán logo hay crop ghép ảnh, CẤM đọc code nguồn `hub_call.py` hay debug backend (dùng trực tiếp tool API đã cấp).
- CẤM tự chạy vòng lặp ReAct dò tìm file ảnh hay crop ảnh thủ công (đã có tool tự động hóa).
- CẤM gọi subagent kiểm chứng độc lập (verifier) vì Graph API đã tự động verify kết quả.
- CẤM dán nguyên văn caption dài hay nhật ký suy luận vào kết quả cuối.
- CẤM bịa post_id hoặc dừng ở bản nháp hỏi lại.
