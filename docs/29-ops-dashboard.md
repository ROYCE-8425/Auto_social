# Bảng Điều Khiển Vận Hành CSKH (Javis Ops — `/ops`)

Phân hệ giao diện độc lập dành riêng cho **Nhân viên CSKH (Staff)** và **Quản lý (Manager)** doanh nghiệp. Giữ nguyên buồng lái console máy chủ (`/app` hoặc `/`) cho **Chủ máy (Owner)**.

---

## 1. Triết lý thiết kế & Cách ly Buồng lái

- **Javis là bộ não ẩn:** Chạy ngầm 24/7, tự động ingest bình luận Fanpage, phân loại ý định, trích xuất SĐT/nhu cầu, và chuẩn bị câu trả lời nháp theo cẩm nang sản phẩm / dịch vụ của thương hiệu (Brand Kit).
- **Console chủ máy (`/app`):** Vẫn là buồng lái kỹ thuật của chủ máy (Terminal, MCP catalog, Chat trực tiếp, Cài đặt model). Nhân viên và Quản lý **bị chặn 403 tuyệt đối**, không thể mở console này.
- **Giao diện `/ops`:** Ứng dụng Single-Page App (React 18, Vite, Tailwind CSS, icon Lucide, font Be Vietnam Pro, màu cam chủ đạo `#f97316`), gọi các REST API sẵn có của Javis mà không sửa đổi bộ não, poller hay engine.

---

## 2. Ma trận Phân quyền (RBAC)

Hệ thống sử dụng module phân quyền mỏng `server/ops_rbac.py` kết hợp lưu trữ tài khoản trong `STATE_DIR/ops_users.json`. Mọi quyền hạn được kiểm tra chặt chẽ ở cấp độ máy chủ (HTTP Middleware 403 thật):

| Thao tác / Khu vực | Nhân viên (Staff) | Quản lý (Manager) | Chủ máy (Owner) |
|---|:---:|:---:|:---:|
| **Xem & Duyệt/Bỏ nháp câu trả lời** | ✓ | ✓ | ✓ |
| **Tạo việc giao người (Handoff)** | ✓ | ✓ | ✓ |
| **Xem danh sách Khách hàng (CRM)** | ✓ (SĐT che `090****567`) | ✓ (Có nút xem đủ) | ✓ |
| **Ghi chú hồ sơ khách hàng** | ✓ | ✓ | ✓ |
| **Xem & Cập nhật Bảng việc (Kanban)** | ✓ | ✓ | ✓ |
| **Messenger: Nhấn "Javis nhận lại"** | ✓ | ✓ | ✓ |
| **Gộp hồ sơ khách hàng trùng lặp** | ✗ (403) | ✓ | ✓ |
| **Xoá hồ sơ khách hàng** | ✗ (403) | ✓ | ✓ |
| **Bấm "Quét bình luận ngay"** | ✗ (403) | ✓ | ✓ |
| **Xem Xu hướng & Báo cáo chi phí Token** | ✗ (403) | ✓ | ✓ |
| **Đổi chế độ Care (`mode=full`)** | ✗ (403) | ✗ (403 - cấm tự động gửi) | ✓ |
| **Bật / Tắt Kill Switch khẩn cấp** | ✗ (403) | ✗ (403) | ✓ |
| **Quản lý cấp tài khoản nhân sự (`/ops/users`)** | ✗ (403) | ✗ (403) | ✓ |
| **Buồng lái console chủ máy (`/`, Terminal, MCP, Chat)** | ✗ (403) | ✗ (403) | ✓ |

---

## 3. Các phân hệ trên giao diện `/ops`

### M1: Tổng quan (Overview)
- **6 Thẻ số liệu thời gian thực:** Bình luận 24h, Lead tiềm năng, Nháp chờ duyệt, Đã phản hồi, Cần người hỗ trợ, Khách hàng tích luỹ.
- **Hộp trạng thái kết nối Fanpage:** Tên Page, chế độ Javis Care (Gợi ý / Bán tự động / Tự động), thời điểm quét gần nhất, cảnh báo Kill Switch.
- **Danh sách nháp mới nhất & Lối tắt xử lý nhanh.**

### M2: Hộp thư & Duyệt câu trả lời (Inbox)
- **Tab 1: Bình luận Fanpage:**
  * Thẻ bình luận thể hiện tên tác giả, nội dung câu hỏi, SĐT bóc tách, nhu cầu/thương hiệu, phân loại ý định (Giá cả, Tư vấn, Đặt hàng, Khuyến mãi...).
  * Khung câu trả lời nháp do Javis soạn: Cho phép **Chỉnh sửa nội dung** trước khi gửi.
  * 3 nút thao tác: **Gửi phản hồi**, **Bỏ qua**, **Tạo việc giao người**.
- **Tab 2: Tin nhắn Messenger:**
  * Danh sách hội thoại đang mở.
  * **Cơ chế Takeover 4 giờ:** Khi nhân viên trả lời khách qua Meta Business Suite, Javis tự lùi lại 4 tiếng để tránh trả lời đè.
  * Nút **"Javis nhận lại"** giúp hoàn trả quyền cho Javis tiếp tục tự động trả lời khi nhân viên đã tư vấn xong.

### M3: Khách hàng (CRM)
- Bảng quản lý khách hàng tiềm năng đã tương tác hoặc để lại số điện thoại.
- Nhân viên thấy SĐT được che dạng `090****567` nhằm bảo mật dữ liệu. Quản lý có nút bật hiện toàn bộ.
- Ngăn trượt chi tiết (Drawer): Xem lịch sử các lượt tương tác, ghi chú nội bộ của tư vấn viên.
- Quản lý có thêm nút **Gộp hồ sơ trùng** và **Xoá hồ sơ**.

### M4: Bảng việc cần làm (Tasks)
- Kanban 3 cột: **Cần làm**, **Đang xử lý**, **Đã hoàn tất**.
- Tự động tiếp nhận công việc khi nhân viên bấm "Tạo việc giao người" ở Hộp thư, hoặc nhân viên có thể bấm "Tạo việc mới".

### M5: Xu hướng & Chi phí (Trends — Quản lý & Chủ máy)
- Biểu đồ phân bổ khách hàng theo thương hiệu / chi nhánh (TP.HCM, Hà Nội, Đà Nẵng...).
- Biểu đồ phân bổ các câu hỏi thường gặp nhất (FAQ).
- Biểu đồ tương tác 7 ngày gần nhất.
- Báo cáo tài nguyên: Tổng token đã sử dụng và ước tính chi phí AI.

### M6: Nhật ký xử lý (Audit Log)
- Dòng thời gian ghi nhận chi tiết mọi hoạt động gửi tin nhắn, duyệt nháp, quét fanpage.

### M7: Quản lý tài khoản (Users — Chỉ Chủ máy)
- Chủ máy đăng nhập bằng tài khoản admin chính có thể tạo thêm tài khoản Nhân viên (Staff) hoặc Quản lý (Manager) cho từng bộ phận / chi nhánh.

---

## 4. Cách triển khai & Vận hành

### Chạy môi trường phát triển (Local Development):
1. **Khởi động server Javis backend:**
   ```bash
   python server/main.py
   ```
2. **Khởi động Ops frontend (nếu cần phát triển giao diện):**
   ```bash
   cd ops
   npm run dev
   ```
   Giao diện chạy tại `http://localhost:5173/ops/` và tự động proxy API sang port 7777.

### Build và phục vụ qua FastAPI:
1. Trong thư mục `ops/`, chạy:
   ```bash
   npm run build
   ```
   Thư mục `ops/dist/` được sinh ra.
2. Truy cập trực tiếp qua địa chỉ: `http://localhost:7777/ops` hoặc qua tên miền đã gắn SSL `https://trannhuy.online/ops`.
