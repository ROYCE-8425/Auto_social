# Kho Tài Liệu & Hợp Đồng Doanh Nghiệp (Document Vault)

## 1. Giới thiệu & Cấu trúc lưu trữ
Kho tài liệu doanh nghiệp (`/ops/#/documents`) là hệ thống lưu trữ và quản lý tài liệu vận hành chính thức của công ty.
- **Lưu trữ file vật lý thật:** `server/storage/documents/{year}/{category}/{safe_filename}`.
- **Cơ sở dữ liệu quản trị:** `server/ops_documents.sqlite3` (`ops_documents_store.py`).
- **Quản lý đa phiên bản (Version control):** Mỗi lần cập nhật file mới được lưu thành phiên bản mới (v1.0, v1.1...) và giữ nguyên lịch sử file cũ.

## 2. Các danh mục tài liệu chuẩn
1. **Hợp đồng (`contract`):** Hợp đồng dịch vụ đào tạo tin học, Hợp đồng cung cấp key bản quyền, Hợp đồng đại lý phân phối, Hợp đồng CTV kinh doanh.
2. **Quy trình SOP (`sop`):** Quy trình tiếp nhận & chốt đơn 5 bước, Quy trình xử lý khiếu nại khách hàng, Quy trình xuất bản nội dung đa kênh.
3. **Biểu mẫu chuẩn (`template`):** Mẫu báo giá dịch vụ BSN, Mẫu hợp đồng đào tạo chuẩn, Biên bản bàn giao tài khoản.
4. **Chính sách (`policy`):** Chính sách bảo hành tài khoản & đổi trả, Chính sách bảo mật thông tin khách hàng, Quy chế thưởng phạt ca trực.
5. **Hóa đơn & Chứng từ (`invoice`):** Chứng từ thanh toán ngân hàng, Hóa đơn VAT điện tử, Biên lai thu tiền học phí.
6. **Pháp lý (`legal`):** Giấy phép đăng ký kinh doanh, Hồ sơ đăng ký nhãn hiệu, Văn bản ủy quyền đại diện.
7. **Nhân sự (`hr`):** Hợp đồng thử việc, Bảng mô tả công việc (JD) nhân viên ca trực, Nội quy lao động.
8. **Marketing & Brand (`marketing`):** Brand Guidelines, Bộ nhận diện thương hiệu, Mẫu banner poster chuẩn.

## 3. Quy trình phê duyệt & Ký số
- **Chờ duyệt (`pending_approval`):** Tài liệu mới tải lên cần Quản lý (Manager/Owner) thẩm định nội dung.
- **Đã duyệt (`approved`):** Tài liệu đạt chuẩn, được ban hành áp dụng nội bộ hoặc cho AI đọc làm căn cứ tư vấn.
- **Đã ký (`signed`):** Hợp đồng đã có chữ ký số điện tử hoặc chữ ký sống kèm dấu mộc.
- **Hết hạn (`expired`):** Tài liệu hết thời hạn hiệu lực pháp lý hoặc cam kết. Hệ thống tự động cảnh báo trước 30 ngày (`is_expiring_soon`).
