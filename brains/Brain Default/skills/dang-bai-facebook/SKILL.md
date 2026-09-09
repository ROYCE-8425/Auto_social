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
    prompt="Banner tuyển sinh thực chiến khóa học <tên_khóa_học_chuẩn> Sao Việt, tiêu đề '<tiêu_đề>', các điểm nổi bật '<highlights>', bố cục chữ và logo nằm trọn trong vùng an toàn cách đều 4 mép ảnh 15-20% (tuyệt đối không để chữ sát mép hay bị cắt mất chữ), phong cách thiết kế hiện đại, không gian học tập công nghệ, nhận diện xanh dương & cam Sao Việt, độ nét cao",
    save_under="attachments/dataset/_xuat",
    ai_render_brand=true
  )
  ```
- Lấy đường dẫn file AI trả về: `res["rel_path"]` (dạng `attachments/dataset/_xuat/cover_...png`).
- **Quy tắc 1-Shot cho Cover AI**: Chỉ gọi `javis_generate_image` đúng 1 lần duy nhất. TUYỆT ĐỐI CẤM loop tạo lại ảnh nhiều lần để soi chính tả hay chữ logo (mô hình khuếch tán AI không thể render typography chính xác 100%, việc cố tạo lại sẽ đốt hàng triệu token và làm nghẽn tiến trình). Dùng trực tiếp ảnh AI sinh ra; phần logo và nhận diện đã có `ai_render_brand=true` xử lý.
- Nếu tool báo lỗi exception hoặc không sinh được file: tối đa retry 1 lần duy nhất. Nếu vẫn thất bại: dừng ngay với `POST_SKIP ly-do=thieu-cover-ai`. TUYỆT ĐỐI CẤM lấy ảnh cũ thay thế và CẤM viết script chèn logo thủ công.

### Bước 2: Soạn Caption Đậm Giá Trị Chuyển Đổi & Đăng ALBUM bằng `fb_page_album`
1. **Xác định Fanpage & Brand Kit**: Đọc đúng 1 file `wiki/brand-kits/<kit-page>.md`. Lấy Page ID, hotline, địa chỉ và chân trang CHAN_TRANG.
2. **Sáng tạo Caption Chuyên Sâu Theo Đúng Ngành Học (Tuyệt đối KHÔNG viết lược bỏ hay nói chung chung)**:
   - Bài viết chuẩn chuyển đổi: 45-65 dòng (chưa tính chân trang), bố cục thoáng, ngắt dòng rõ ràng, đọc lướt mobile cực kỳ cuốn hút.
   - **BẮT BUỘC nạp và đưa kiến thức chi tiết từ `wiki/courses/<the>.md` vào thân bài**:
     * **Tiêu đề IN HOA + Icon Hook**: Đánh trúng nhu cầu cấp bách của ngành (ví dụ AutoCAD: `KHÓA HỌC AUTOCAD 2D & 3D THỰC CHIẾN - ĐỌC HIỂU & TRIỂN KHAI BẢN VẼ CHUẨN KỸ THUẬT`; Kế toán: `KHÓA HỌC KẾ TOÁN THỰC HÀNH TỔNG HỢP TRÊN CHỨNG TỪ SỐNG & MISA`; Đồ họa: `KHÓA HỌC THIẾT KẾ ĐỒ HỌA CHUYÊN NGHIỆP - THÀNH THẠO PHOTOSHOP & ILLUSTRATOR`).
     * **Đoạn mở đầu (3-4 dòng)**: Nêu rõ đối tượng phù hợp (sinh viên, người đi làm, người cần bổ sung kỹ năng đi làm ngay) và bài toán thực tế họ đang gặp phải.
     * **Khối nội dung chương trình & công cụ đào tạo chi tiết (BẮT BUỘC - 8-12 dòng)**:
       - Với AutoCAD (`ve-ky-thuat`): Liệt kê rõ làm chủ hệ thống lệnh vẽ 2D từ cơ bản đến nâng cao, quản lý Layer chuyên nghiệp, Block động, Dim kích thước chuẩn ISO, dàn trang Layout và in ấn xuất bản vẽ PDF đúng tỷ lệ kỹ thuật, kỹ năng đọc và bóc tách khối lượng từ hồ sơ bản vẽ công trình / cơ khí thực tế.
       - Với Kế toán (`ke-toan`): Liệt kê rõ thực hành xử lý hóa đơn chứng từ sống 100%, thao tác thành thạo phần mềm MISA SME phiên bản mới nhất, kỹ năng lập sổ sách và bảng lương trên Excel chuyên sâu, kê khai thuế định kỳ qua HTKK/iTaxViewer, lập Báo cáo tài chính (BCTC) cuối năm chuẩn quy định cho các mô hình DN (thương mại, dịch vụ, sản xuất, xây lắp...).
       - Với Đồ họa (`do-hoa`): Liệt kê rõ thành thạo Adobe Photoshop (chỉnh sửa ảnh, cắt ghép, blend màu, thiết kế banner quảng cáo Facebook/Google), Adobe Illustrator (thiết kế logo vector, bộ nhận diện, bao bì, infographic), CorelDRAW / InDesign (dàn trang catalogue, brochure, xuất file in offset chuẩn 4 màu CMYK), tư duy bố cục, phối màu, hoàn thiện portfolio cá nhân.
       - Với Tin học (`tin-hoc _ai`): Liệt kê rõ Word soạn thảo văn bản hành chính theo quy chuẩn, Excel hàm nâng cao (VLOOKUP, XLOOKUP, INDEX/MATCH), PivotTable, tạo Dashboard báo cáo động tự động, PowerPoint thiết kế slide thuyết trình ấn tượng, tích hợp trợ lý AI (ChatGPT, Copilot) tối ưu hóa công việc văn phòng, luyện thi chứng chỉ quốc tế MOS/IC3.
     * **Khối cam kết & phương pháp đào tạo vàng tại Sao Việt (5-6 dòng, bắt đầu bằng `📌`)**:
       - `📌 Đào tạo kèm 1-1 trực tiếp trên máy, giáo viên kèm sát theo tiến độ của từng học viên.`
       - `📌 Học thực hành 100% trên bài tập và tài liệu thực tế của doanh nghiệp, không học lý thuyết suông.`
       - `📌 Cam kết học đến khi thành thạo, không giới hạn số buổi học.`
       - `📌 Lịch học linh hoạt ca sáng - chiều - tối từ Thứ 2 đến Thứ 7, đăng ký là học ngay không cần chờ lớp.`
       - `📌 Hỗ trợ cài đặt phần mềm và giải đáp nghiệp vụ chuyên môn trong suốt quá trình đi làm.`
     * **Khối quyền lợi & quà tặng hỗ trợ (3-4 dòng, bắt đầu bằng `🎁`)**:
       - `🎁 Được tư vấn lộ trình học phù hợp với ngành nghề và mục tiêu công việc cá nhân.`
       - `🎁 Được cấp trọn bộ tài liệu, giáo trình thực hành và file mẫu chuẩn của trung tâm.`
       - `🎁 Nhận chứng chỉ hoàn thành khóa học có giá trị xác nhận kỹ năng thực tế.`
     * **Khối Kêu gọi hành động (CTA) dứt khoát (3 dòng)**:
       - `👉 Bạn cần học cấp tốc để phục vụ công việc hoặc nâng cao chuyên môn?`
       - `📞 Nhắn tin trực tiếp cho Fanpage hoặc liên hệ Hotline/Zalo để nhận lộ trình và ưu đãi học phí tốt nhất!`
       - `📌 Khai giảng lớp mới liên tục mỗi tuần, xếp ca học theo thời gian rảnh của bạn.`
     * **Chân trang CHAN_TRANG**: BẮT BUỘC dùng đúng định dạng sạch từ `pick_next_fanpage.py` hoặc brand kit:
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
