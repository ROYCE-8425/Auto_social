---
name: Đăng bài Facebook
description: "Đăng bài Fanpage Sao Việt: Album 6-8 ảnh chuẩn Tỷ Lệ Vàng 2026 (1 cover AI mới 100% + ảnh lớp học thật dataset), luân phiên 4 góc nội dung (Mẹo thực chiến, Tình huống nghề, Tặng tài liệu, Tuyển sinh) kèm chân trang chuẩn."
group: Facebook
---

# Đăng bài Facebook - Album 6-8 Ảnh Chuẩn Tỷ Lệ Vàng 2026

Mục tiêu: Mỗi bài đăng Fanpage là một **ALBUM chuẩn Tỷ Lệ Vàng Facebook 2026 (ngẫu nhiên 6, 7 hoặc 8 ảnh)** gồm: 1 ảnh bìa độc quyền do GPT Image 2 (`javis_generate_image`) tạo mới 100% + 5-7 ảnh chụp lớp học thật từ dataset đi kèm, đăng tự động bằng `fb_page_album` với `photos='auto'`.

## Quy ước đường dẫn làm việc (Cấm mất thời gian mò file):
- **Môi trường VPS (chạy Việc định kỳ / container Docker, thư mục làm việc là vault)**:
  * Script điều phối: `python skills/dang-bai-facebook/scripts/pick_next_fanpage.py`
  * Brand Kit: `wiki/brand-kits/<kit>`
  * Khóa học: `wiki/courses/<the>.md`
  * Dataset ảnh lớp học thật: `attachments/dataset/<the>/`
  * Nơi lưu ảnh xuất AI: `attachments/dataset/_xuat/`
- **Môi trường Local (chạy từ thư mục gốc project `javis-os`)**:
  * Thêm tiền tố `brains/Brain Default/` vào trước đường dẫn (ví dụ: `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"`).

## Luồng thực hiện chuẩn 2 bước:

Hệ thống tự động điều phối bài viết theo **4 Góc Nội Dung (Content Pillars)** qua biến `angle` từ output của `pick_next_fanpage.py`:
1. `meo_thuc_chien`: Mẹo & Thủ thuật / Phím tắt thực chiến (Tips & Tricks - Chia sẻ giá trị).
2. `tinh_huong`: Tình huống thực tế & Giải pháp nghề nghiệp (Troubleshooting & Case study).
3. `tai_lieu`: Tặng tài liệu & Thư viện file mẫu (Lead Magnet / Free Resources).
4. `tuyen_sinh`: Tuyển sinh & Khai giảng lớp mới kèm 1-1 (Direct Enrollment).

---

### Bước 1: BẮT BUỘC tạo 1 ảnh bìa mới 100% bằng GPT Image 2 (Theo đúng `angle`)
- Đọc file `wiki/courses/<the>.md` (hoặc `course_path` từ output của script) để lấy Tiêu đề và nội dung chuyên môn tương ứng với `angle`.
- GỌI THẲNG TOOL DUY NHẤT `javis_generate_image` với prompt chuẩn theo từng góc:

  * **Nếu `angle == "meo_thuc_chien"` (Mẹo & Thủ thuật)**:
    ```text
    javis_generate_image(
      prompt="Infographic poster kiến thức mẹo thủ thuật kỹ thuật chuyên ngành <the> Sao Việt, tiêu đề nổi bật '<tiêu_đề_mẹo>', các bước hướng dẫn hoặc phím tắt trực quan, bố cục chữ và hình nằm trọn trong vùng an toàn cách đều 4 mép ảnh 15-20% (tuyệt đối không để chữ sát mép hay bị cắt chữ), phong cách thiết kế đồ họa công nghệ hiện đại, nhận diện xanh dương & cam Sao Việt, độ nét cao, TUYỆT ĐỐI KHÔNG CÓ chữ tuyển sinh, KHÔNG CÓ nút đăng ký",
      save_under="attachments/dataset/_xuat",
      ai_render_brand=true
    )
    ```

  * **Nếu `angle == "tinh_huong"` (Tình huống thực tế / Xử lý lỗi)**:
    ```text
    javis_generate_image(
      prompt="Poster chuyên đề giải pháp kỹ thuật và xử lý tình huống thực tế ngành <the> Sao Việt, tiêu đề nổi bật '<tiêu_đề_tình_huống>', phân tích giải pháp công nghệ trực quan, bố cục nằm trọn trong vùng an toàn cách đều 4 mép ảnh 15-20%, phong cách thiết kế hiện đại, nhận diện xanh dương & cam Sao Việt, độ nét cao, TUYỆT ĐỐI KHÔNG CÓ chữ tuyển sinh, KHÔNG CÓ nút đăng ký",
      save_under="attachments/dataset/_xuat",
      ai_render_brand=true
    )
    ```

  * **Nếu `angle == "tai_lieu"` (Tặng tài liệu / File mẫu)**:
    ```text
    javis_generate_image(
      prompt="Poster chia sẻ tài liệu và thư viện file mẫu thực hành chuyên ngành <the> Sao Việt, tiêu đề nổi bật 'BỘ TÀI LIỆU & FILE MẪU CHUẨN THỰC CHIẾN', hình ảnh minh họa tài nguyên template trực quan, vùng an toàn cách đều 4 mép 15-20%, phong cách hiện đại công nghệ, nhận diện xanh dương & cam Sao Việt, độ nét cao, TUYỆT ĐỐI KHÔNG CÓ chữ tuyển sinh, KHÔNG CÓ nút đăng ký",
      save_under="attachments/dataset/_xuat",
      ai_render_brand=true
    )
    ```

  * **Nếu `angle == "tuyen_sinh"` (Tuyển sinh trực tiếp)**:
    ```text
    javis_generate_image(
      prompt="Banner tuyển sinh thực chiến khóa học <the> Sao Việt, tiêu đề '<tiêu_đề>', các điểm nổi bật '<highlights>', bố cục chữ và logo nằm trọn trong vùng an toàn cách đều 4 mép ảnh 15-20% (tuyệt đối không để chữ sát mép hay bị cắt mất chữ), phong cách thiết kế hiện đại, không gian học tập công nghệ, nhận diện xanh dương & cam Sao Việt, độ nét cao",
      save_under="attachments/dataset/_xuat",
      ai_render_brand=true
    )
    ```

- Lấy đường dẫn file AI trả về: `res["rel_path"]` (dạng `attachments/dataset/_xuat/cover_...png`).
- **Quy tắc 1-Shot cho Cover AI**: Chỉ gọi `javis_generate_image` đúng 1 lần duy nhất. TUYỆT ĐỐI CẤM loop tạo lại ảnh nhiều lần để soi chính tả hay chữ logo (mô hình khuếch tán AI không thể render typography chính xác 100%, việc cố tạo lại sẽ đốt hàng triệu token và làm nghẽn tiến trình). Dùng trực tiếp ảnh AI sinh ra; phần logo và nhận diện đã có `ai_render_brand=true` xử lý.
- Nếu tool báo lỗi exception hoặc không sinh được file: tối đa retry 1 lần duy nhất. Nếu vẫn thất bại: dừng ngay với `POST_SKIP ly-do=thieu-cover-ai`. TUYỆT ĐỐI CẤM lấy ảnh cũ thay thế và CẤM viết script chèn logo thủ công.

---

### Bước 2: Soạn Caption Đậm Giá Trị Chuyên Môn & Đăng ALBUM bằng `fb_page_album`
1. **Xác định Fanpage & Brand Kit**: Đọc đúng 1 file `wiki/brand-kits/<kit-page>.md`. Lấy Page ID, hotline, địa chỉ và chân trang CHAN_TRANG.
2. **Sáng tạo Caption Chuyên Sâu Theo Đúng Ngành Học & Đúng Góc Nội Dung (`angle`)**:
   - Bài viết chuẩn chuyển đổi: 45-65 dòng (chưa tính chân trang), bố cục thoáng, ngắt dòng rõ ràng, đọc lướt mobile cực kỳ cuốn hút.
   - Viết theo đúng khung sườn của `angle`:

   #### A. Khung bài Góc 1: Mẹo & Thủ thuật / Phím tắt thực chiến (`angle == "meo_thuc_chien"`)
   * **Tiêu đề IN HOA + Icon Hook**:
     - AutoCAD: `💡 5 LỆNH TẮT AUTOCAD VẼ NHANH GẤP 3 LẦN CHO DÂN KỸ THUẬT`
     - Kế toán: `💡 7 LỖI HÓA ĐƠN ĐIỆN TỬ DỄ BỊ PHẠT & CÁCH XỬ LÝ NHANH TRONG 5 PHÚT`
     - Đồ họa: `💡 10 PHÍM TẮT PHOTOSHOP GIÚP THIẾT KẾ NHANH GẤP ĐÔI`
     - Tin học: `💡 5 HÀM EXCEL THAY THẾ HOÀN TOÀN VLOOKUP KHI ĐI LÀM`
   * **Đoạn mở đầu (2-3 dòng)**: Nêu rõ khó khăn khi thao tác thủ công, mất thời gian và mục tiêu của các mẹo này giúp tối ưu công việc ra sao.
   * **Chi tiết 4-5 mẹo thực chiến (12-18 dòng)**:
     - Với mỗi mẹo: Nêu tên phím tắt/lệnh + Công dụng thực tế + Các bước thao tác 1-2-3 rõ ràng, dễ hiểu.
     - Đưa kiến thức thực tế bám sát chuyên môn của ngành đó (AutoCAD: F8, LAYOFF, MA, STRETCH, PURGE; Kế toán: kiểm tra mã CQT, đối chiếu ngày lập/ký, xử lý hóa đơn điều chỉnh; Đồ họa: Ctrl+J, Alt+Delete, clipping mask, brush hardness; Tin học: XLOOKUP, UNIQUE, FILTER, phím tắt F4, Ctrl+E Flash Fill).
   * **Lời khuyên & CTA mềm (4-5 dòng)**:
     - `👉 Lưu lại bài viết ngay để khi cần lấy ra áp dụng!`
     - `💬 Bạn thường dùng mẹo nào nhất hoặc đang gặp vướng mắc ở thao tác nào? Bình luận bên dưới để Sao Việt giải đáp nhé.`
     - `📌 Bạn cần học bài bản từ gốc, nâng cao kỹ năng để tự tin đi làm? Tham khảo ngay các khóa đào tạo kèm 1-1 tại Tin Học Sao Việt.`
   * **Chân trang CHAN_TRANG**: Nối nguyên khối chân trang chuẩn.

   #### B. Khung bài Góc 2: Tình huống thực tế & Giải pháp nghề nghiệp (`angle == "tinh_huong"`)
   * **Tiêu đề IN HOA + Icon Hook**:
     - AutoCAD: `⚙️ BẢN VẼ AUTOCAD BỊ NẶNG, GIẬT LAG? 3 BƯỚC KHẮC PHỤC TRIỆT ĐỂ TRONG 30 GIÂY`
     - Kế toán: `📑 HÓA ĐƠN ĐẦU VÀO SAI SỐ TIỀN HOẶC MÃ SỐ THUẾ? QUY TRÌNH XỬ LÝ CHUẨN THEO TT 78`
     - Đồ họa: `🎨 CÁCH TÁCH TÓC MẪU TRONG PHOTOSHOP KHÔNG BỊ LEM VIỀN TRẮNG BẰNG SELECT & MASK`
     - Tin học: `📊 CÁCH TẠO BÁO CÁO DASHBOARD ĐỘNG BẰNG PIVOTTABLE TỰ ĐỘNG CẬP NHẬT SỐ LIỆU`
   * **Đoạn mở đầu (2-3 dòng)**: Đặt tình huống thực tế hay gặp trong công việc khiến nhiều người bối rối.
   * **Phân tích nguyên nhân gốc rễ (3-4 dòng)**: Giải thích vì sao lỗi đó lại phát sinh.
   * **Hướng dẫn giải pháp từng bước (10-15 dòng)**:
     - Bước 1: Chuẩn bị / Kiểm tra dữ liệu.
     - Bước 2: Thao tác khắc phục chi tiết với phần mềm.
     - Bước 3: Kiểm tra lại và lưu trữ quy chuẩn để không bị lặp lại lỗi.
   * **Kinh nghiệm thực chiến từ chuyên gia + CTA mềm**:
     - `👉 Đừng quên chia sẻ bài viết cho đồng nghiệp cùng biết nhé!`
     - `📌 Bạn muốn thành thạo xử lý mọi tình huống thực tế trong công việc? Tham khảo các chương trình đào tạo kèm 1-1 tại Tin Học Sao Việt.`
   * **Chân trang CHAN_TRANG**.

   #### C. Khung bài Góc 3: Tặng tài liệu & Thư viện file mẫu (`angle == "tai_lieu"`)
   * **Tiêu đề IN HOA + Icon Hook**:
     - AutoCAD: `🎁 CHIA SẺ TRỌN BỘ THƯ VIỆN BLOCK CAD 2D THỰC CHIẾN (CỬA, NỘI THẤT, CÂY, THIẾT BỊ VỆ SINH)`
     - Kế toán: `🎁 TẶNG FILE MẪU EXCEL BẢNG CHẤM CÔNG & TÍNH LƯƠNG TỰ ĐỘNG MỚI NHẤT 2026`
     - Đồ họa: `🎁 TỔNG HỢP 500+ FONT CHỮ VIỆT HÓA CHUYÊN DÙNG CHO THIẾT KẾ QUẢNG CÁO & SOCIAL`
     - Tin học: `🎁 TRỌN BỘ 30+ MẪU SLIDE POWERPOINT THUYẾT TRÌNH BÁO CÁO DOANH NGHIỆP HIỆN ĐẠI`
   * **Nội dung bộ quà tặng (8-12 dòng)**:
     - Liệt kê chi tiết danh mục tài nguyên có trong bộ quà tặng.
     - Đánh giá giá trị thực tế: Tiết kiệm hàng chục giờ dựng file thủ công, áp dụng được ngay vào công việc.
     - Chuẩn định dạng, tương thích mọi phiên bản phần mềm.
   * **Cách thức nhận quà (3-4 dòng)**:
     - `👉 Nhắn tin trực tiếp cho Fanpage hoặc để lại bình luận bên dưới để nhận trọn bộ link tải hoàn toàn miễn phí!`
     - `📌 Đừng quên theo dõi Fanpage để cập nhật thêm nhiều bộ tài liệu chuyên ngành hữu ích tiếp theo.`
   * **Chân trang CHAN_TRANG**.

   #### D. Khung bài Góc 4: Tuyển sinh / Khai giảng khóa kèm 1-1 (`angle == "tuyen_sinh"`)
   * **Tiêu đề IN HOA + Icon Hook**: Đánh trúng nhu cầu học đi làm (AutoCAD: `KHÓA HỌC AUTOCAD 2D & 3D THỰC CHIẾN - ĐỌC HIỂU & TRIỂN KHAI BẢN VẼ CHUẨN KỸ THUẬT`; Kế toán: `KHÓA HỌC KẾ TOÁN THỰC HÀNH TỔNG HỢP TRÊN CHỨNG TỪ SỐNG & MISA`; Đồ họa: `KHÓA HỌC THIẾT KẾ ĐỒ HỌA CHUYÊN NGHIỆP - THÀNH THẠO PHOTOSHOP & ILLUSTRATOR`; Tin học: `KHÓA HỌC TIN HỌC VĂN PHÒNG & ỨNG DỤNG AI THỰC CHIẾN`).
   * **Đoạn mở đầu (3-4 dòng)**: Nêu rõ đối tượng phù hợp và bài toán cần giải quyết.
   * **Khối nội dung chương trình đào tạo chi tiết (8-12 dòng)**: Liệt kê rõ công cụ, bài tập thực hành sát thực tế doanh nghiệp.
   * **Khối cam kết & phương pháp đào tạo vàng tại Sao Việt (5 dòng, bắt đầu bằng `📌`)**:
     - `📌 Đào tạo kèm 1-1 trực tiếp trên máy, giáo viên kèm sát theo tiến độ của từng học viên.`
     - `📌 Học thực hành 100% trên bài tập và tài liệu thực tế của doanh nghiệp, không học lý thuyết suông.`
     - `📌 Cam kết học đến khi thành thạo, không giới hạn số buổi học.`
     - `📌 Lịch học linh hoạt ca sáng - chiều - tối từ Thứ 2 đến Thứ 7, đăng ký là học ngay không cần chờ lớp.`
     - `📌 Hỗ trợ cài đặt phần mềm và giải đáp nghiệp vụ chuyên môn trong suốt quá trình đi làm.`
   * **Khối quyền lợi (3 dòng, bắt đầu bằng `🎁`)**:
     - `🎁 Được tư vấn lộ trình học phù hợp với ngành nghề và mục tiêu công việc cá nhân.`
     - `🎁 Được cấp trọn bộ tài liệu, giáo trình thực hành và file mẫu chuẩn của trung tâm.`
     - `🎁 Nhận chứng chỉ hoàn thành khóa học có giá trị xác nhận kỹ năng thực tế.`
   * **Khối Kêu gọi hành động (CTA) dứt khoát (3 dòng)**:
     - `👉 Bạn cần học cấp tốc để phục vụ công việc hoặc nâng cao chuyên môn?`
     - `📞 Nhắn tin trực tiếp cho Fanpage hoặc liên hệ Hotline/Zalo để nhận lộ trình và ưu đãi học phí tốt nhất!`
     - `📌 Khai giảng lớp mới liên tục mỗi tuần, xếp ca học theo thời gian rảnh của bạn.`
   * **Chân trang CHAN_TRANG**.

   #### Quy chuẩn định dạng chân trang CHAN_TRANG (Áp dụng cho TẤT CẢ các góc bài):
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
   `POST_OK post_id=<post_id> status=verified link=https://www.facebook.com/<post_id> | <Trang> | <Khóa học> | <Góc: meo_thuc_chien / tinh_huong / tai_lieu / tuyen_sinh> | Album 6-8 ảnh`

## Quy định nghiêm ngặt:
- Nếu `pick_next_fanpage.py` trả về `NEXT=NONE` (ví dụ `page-da-ok-hom-nay` hoặc `het-hang-hom-nay`): DỪNG NGAY TIẾN TRÌNH, không được dùng `--page` để bypass hoặc cố đăng tiếp.
- TUYỆT ĐỐI CẤM dùng cover cũ trong `_xuat`. Cover luôn luôn là ảnh AI mới tạo 100%.
- CẤM loop retry tạo cover AI vì lý do chữ nhỏ hay logo. Đúng 1 lần tạo là dùng.
- CẤM tự viết script Python (Pillow/cv2) để dán logo hay crop ghép ảnh, CẤM đọc code nguồn `hub_call.py` hay debug backend (dùng trực tiếp tool API đã cấp).
- CẤM tự chạy vòng lặp ReAct dò tìm file ảnh hay crop ảnh thủ công (đã có tool tự động hóa).
- CẤM gọi subagent kiểm chứng độc lập (verifier) vì Graph API đã tự động verify kết quả.
- CẤM dán nguyên văn caption dài hay nhật ký suy luận vào kết quả cuối.
- CẤM bịa post_id hoặc dừng ở bản nháp hỏi lại.
