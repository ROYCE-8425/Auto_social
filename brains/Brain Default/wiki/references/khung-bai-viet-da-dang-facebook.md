# Khung Bài Viết Đa Dạng Facebook — Hệ Thống Sao Việt

Tài liệu tham chiếu các cấu trúc bài viết thực chiến (Caption Frameworks) được kế thừa và chuẩn hóa cho toàn bộ hệ thống Fanpage Tin Học Sao Việt, AutoCAD Sao Việt, Kế Toán Sao Việt và Đồ Họa Sao Việt.

---

## 1. NGUYÊN TẮC VÀNG TRƯỚC KHI VIẾT

- **Plain Text 100%**: Tuyệt đối không dùng Markdown in đậm `**` hay heading `#` trong bài đăng Facebook/Zalo. Nếu cần nhấn mạnh: dùng CHỮ HOA vừa phải, emoji, xuống dòng và gạch đầu dòng.
- **Độ dài tối ưu đọc lướt di động**: 28 đến 45 dòng thân bài (chưa tính chân trang). Câu ngắn, 1-2 câu ngắt dòng 1 lần, thoáng mắt.
- **Không văn mẫu AI**: Cấm mở bài bằng "Bạn có biết", "Trong thời đại 4.0", "Chiến dịch tuyển sinh", "Đột phá/vượt trội/đỉnh cao". Đi thẳng vào tình huống thực tế của học viên.
- **Nhịp thị giác Emoji theo ngành**:
  * **AutoCAD / Kỹ thuật**: `📐 🏗️ 🧱 🛠️ 📏 ⚙️`
  * **Kế toán**: `📊 🧾 💼 💰 📌 📑`
  * **Đồ họa**: `🎨 🖌️ 🖼️ ✂️ ✨`
  * **Tin học & AI**: `💻 🤖 ⚡ 🧠 ⏱️ 🚀`
  * **Icon dẫn dắt chung**: `🔵 📍 📌 👉 ✅ ❌ 💡 🎁 📞 🌐`

---

## 2. 6 MÔ HÌNH BÀI VIẾT THỰC CHIẾN ĐA DẠNG

### Khung 1: Checklist Tự Đánh Giá Kỹ Năng (Self-Assessment)
> **Mục tiêu**: Kích thích người xem tự soi lại tay nghề đi làm của mình, nhận diện lỗ hổng kiến thức.

- **Hook mở đầu (1-2 dòng)**:
  `🔵 Vẽ được hình AutoCAD nhưng in ra có chắc đúng tỷ lệ không?` (hoặc `🔵 Làm kế toán 1 năm, bạn đã tự tin tự lập Báo cáo tài chính chưa?`)
- **Đoạn dẫn nhập**: Đi làm thực tế không chỉ là biết vài thao tác cơ bản, mà phải làm đúng chuẩn doanh nghiệp.
- **Khối Checklist 4-5 câu hỏi (Dùng icon ngành + `Đã biết... chưa?`)**:
  * `📐 Đã biết quản lý Layer theo chuẩn màu và nét in chưa?`
  * `📏 Đã biết ghi kích thước Dimstyle và dùng lệnh MV chia khung nhìn Layout chưa?`
  * `🛠️ Đã biết tạo Block thuộc tính và lọc bản vẽ bằng lệnh QSELECT chưa?`
  * `🏗️ Đã biết setup bảng nét in .ctb để khi in bản vẽ không bị lem nét chưa?`
  * `✅ Đã tự triển khai được một bản vẽ hoàn chỉnh từ sơ đồ phác thảo chưa?`
- **Chuyển tiếp giải pháp**:
  `📌 Nếu còn vướng 2-3 mục ở trên, thay vì tiếp tục tự mò mẫm mất hàng tháng trời, bạn nên tham gia khóa học thực hành kèm 1-1...`
- **Khối tóm tắt chương trình (4-5 dòng)**: Nêu rõ các module xử lý dứt điểm các lỗi trên.
- **CTA mềm + Chân trang CHAN_TRANG**.

---

### Khung 2: Mini Case Trước & Sau Thực Tế (Before / After Transformation)
> **Mục tiêu**: Kể chuyện chuyển đổi (storytelling) giữa cách làm thủ công và cách làm thông minh.

- **Hook mở đầu (1-2 dòng)**:
  `🔵 Một báo cáo tổng hợp mất 2 tiếng, bạn hoàn toàn có thể rút ngắn còn 15 phút nếu biết kết hợp Excel và AI.`
- **Thực trạng làm thủ công (Nỗi đau)**:
  * `❌ Ngồi dò từng dòng dữ liệu bằng mắt, dễ nhầm lẫn số liệu.`
  * `❌ Viết công thức dài ngoằng nhưng thường xuyên bị lỗi #N/A, #VALUE!.`
  * `❌ Cuối tháng thức khuya tăng ca chỉ để xử lý các bảng tính lặp đi lặp lại.`
- **Giải pháp chuyển đổi thực tế (Thành quả)**:
  * `⚡ Sử dụng các hàm thế hệ mới (XLOOKUP, FILTER, UNIQUE) lọc tự động trong 1 giây.`
  * `🤖 Tận dụng AI tạo dàn ý báo cáo, viết prompt phân tích số liệu chuẩn xác.`
  * `📊 Thiết lập Dashboard động bằng PivotTable tự nhảy biểu đồ khi thêm dòng mới.`
- **Giới thiệu lớp học kèm 1-1**: Nêu rõ phương pháp cầm tay chỉ việc, học trên số liệu thật.
- **CTA + Chân trang CHAN_TRANG**.

---

### Khung 3: Giải Phẫu Sự Cố & Lỗi Thường Gặp (Troubleshooting)
> **Mục tiêu**: Cứu nguy kỹ thuật, chia sẻ giá trị chuyên môn cao, xây dựng uy tín chuyên gia.

- **Hook mở đầu (1-2 dòng)**:
  `💡 3 LỖI HÓA ĐƠN ĐIỆN TỬ DỄ BỊ CƠ QUAN THUẾ PHẠT & QUY TRÌNH XỬ LÝ THEO TT 78`
- **Đặt tình huống sự cố**: Gặp hóa đơn sai mã số thuế, sai ngày ký và ngày lập, hoặc sai đơn giá thành tiền.
- **Các bước xử lý chuẩn 1-2-3**:
  * `Bước 1: Lập biên bản thỏa thuận giữa hai bên về sai sót.`
  * `Bước 2: Phát hành hóa đơn điều chỉnh hoặc hóa đơn thay thế trên phần mềm hóa đơn điện tử.`
  * `Bước 3: Lập mẫu 04/SS-HĐĐT gửi cơ quan thuế và lưu trữ hồ sơ đối chiếu.`
- **Lời khuyên nghề nghiệp**:
  `👉 Lưu ngay bài viết này để khi gặp sự cố lấy ra xử lý đúng quy định!`
- **CTA tham khảo khóa học kèm 1-1 + Chân trang CHAN_TRANG**.

---

### Khung 4: Lộ Trình Đào Tạo Phân Tầng (Roadmap Breakdown)
> **Mục tiêu**: Khách hàng thấy rõ con đường từ mất gốc/chưa biết gì đến khi thành thạo đi làm.

- **Hook mở đầu (1-2 dòng)**:
  `🚀 LỘ TRÌNH TỪ CON SỐ 0 ĐẾN THÀNH THẠO [TÊN_KHÓA_HỌC] CHO NGƯỜI ĐI LÀM`
- **Khối lộ trình phân tầng**:
  * `📍 Tuần 1-2: Nắm vững nền tảng & công cụ cốt lõi.`
  * `📍 Tuần 3-4: Thực hành xử lý dự án / hồ sơ chứng từ thực tế của doanh nghiệp.`
  * `📍 Tuần 5-6: Nâng cao tốc độ thao tác, phím tắt và xử lý các ca lỗi phức tạp.`
  * `📍 Hoàn thành: Tự tin ứng tuyển, triển khai công việc độc lập.`
- **Cam kết đào tạo Sao Việt**:
  * `📌 Học kèm 1-1 trực tiếp trên máy tính.`
  * `📌 Không giới hạn số buổi học, học đến khi thành thạo.`
  * `📌 Lịch học linh hoạt sáng/chiều/tối từ Thứ 2 đến Thứ 7.`
- **CTA + Chân trang CHAN_TRANG**.

---

### Khung 5: Mẹo Phím Tắt & Thao Tác Tốc Độ (Quick Tips & Tricks)
> **Mục tiêu**: Chia sẻ giá trị ngắn gọn, dễ share, dễ lưu bài viết.

- **Hook mở đầu (1-2 dòng)**:
  `💡 5 PHÍM TẮT PHOTOSHOP GIÚP TỐI ƯU TỐC ĐỘ THIẾT KẾ BẠN CẦN BIẾT`
- **Nội dung 4-5 mẹo chi tiết**: Nêu tên phím tắt + Tác dụng thực tế + Cách bấm.
- **Lời kêu gọi mềm**:
  `👉 Thử áp dụng ngay hôm nay để thấy tốc độ làm việc cải thiện rõ rệt!`
  `💬 Bạn muốn Sao Việt làm tiếp mẹo về chủ đề nào? Hãy bình luận bên dưới nhé.`
- **Chân trang CHAN_TRANG**.

---

### Khung 6: Tuyển Sinh Trực Tiếp Chuyên Sâu (Direct Enrollment)
> **Mục tiêu**: Chuyển đổi đăng ký lớp học mới, giải quyết trọn vẹn rào cản thời gian và học phí.

- **Hook mở đầu**: Đánh trúng mục tiêu học để đổi nghề, học để nâng lương, học để đáp ứng việc công ty.
- **Nội dung chương trình đào tạo**: Liệt kê 4-6 kỹ năng cốt lõi được đào tạo.
- **Khối cam kết vàng (`📌`)**:
  * `📌 Giảng viên kèm 1-1 sát theo năng lực từng học viên.`
  * `📌 Học thực hành 100% trên bài tập và số liệu thực tế.`
  * `📌 Cam kết học đến khi thành thạo, không giới hạn số buổi.`
  * `📌 Đăng ký là xếp lịch học ngay, không phải chờ mở lớp.`
- **Khối quyền lợi (`🎁`)**: Cấp tài liệu, giáo trình, chứng chỉ hoàn thành khóa học.
- **CTA dứt khoát**: Nhắn tin Fanpage hoặc Hotline/Zalo để xếp ca học gần nhất.
- **Chân trang CHAN_TRANG**.
