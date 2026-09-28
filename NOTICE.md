# NOTICE

Dự án **Sèo Trum** (repository: `ROYCE-8425/Auto_social`) được phát triển dựa trên nền tảng mã nguồn mở **Javis OS** dưới giấy phép MIT License:
- Upstream project: [Javis OS](https://github.com/blogminhquy/javis-os)
- Copyright (c) 2026 Nguyễn Minh Quý (blogminhquy)

---

## Nền tảng & Lớp Nghiệp vụ Mở rộng (Extensions & Additions)

Dự án **Sèo Trum** kế thừa kiến trúc nhân tác tử (AI Agentic Kernel & MCP Hub) từ Javis OS, đồng thời tập trung nghiên cứu, thiết kế và phát triển mới hoàn toàn lớp nghiệp vụ vận hành, phân phối nội dung đa kênh và chăm sóc khách hàng tự động cho doanh nghiệp vừa và nhỏ (SME):

1. **Sèo Trum Ops (`/ops`)**:
   - Giao diện Web SPA (React 18 + TailwindCSS + Vite) thiết kế riêng biệt cho nhân viên trực ca CSKH (Staff) và quản lý (Manager).
   - Hệ thống phân quyền truy cập RBAC 3 cấp (`staff`, `manager`, `owner`) với cơ chế phòng thủ nghiêm ngặt (HTTP 403 fail-closed), tách biệt hoàn toàn dữ liệu vận hành hàng ngày khỏi buồng lái máy chủ (`/app`).

2. **Hộp thư Hợp nhất & Chăm sóc Khách hàng (Fanpage & Messenger Care Engine)**:
   - Thu thập bình luận Fanpage và tin nhắn Messenger tự động thời gian thực.
   - Bộ phân loại ý định (Rules-first Intent Classifier) kết hợp AI, nhận diện câu hỏi giá, tư vấn sản phẩm, khiếu nại.
   - Trích xuất số điện thoại (Phone Extractor) bằng Regex đa định dạng của Việt Nam.
   - Cơ chế **Human-in-the-Loop 1-Click Duyệt gửi**: AI soạn nháp trả lời chuẩn theo Brand Kit trong 30 giây, nhân viên kiểm duyệt trước khi phát hành, triệt tiêu 100% rủi ro AI ảo giác (anti-hallucination).

3. **Trung tâm Phân phối Đa Kênh & Tự động hóa TikTok (Social Channels Hub)**:
   - Điều phối tập trung 4 nền tảng mạng xã hội: Facebook Fanpage & Messenger, TikTok Video & Shop, Instagram & Threads, YouTube Shorts.
   - Cổng kết nối TikTok Gateway (PostPeer BYO key) hỗ trợ xuất bản video dọc 9:16 và album ảnh carousel kèm nhạc nền hot trend (`autoAddMusic`), phục vụ media an toàn qua endpoint `/tiktok-media`.

4. **Multi-Brand CRM & Chấm điểm Lead Tự động**:
   - Quản lý hồ sơ khách hàng hợp nhất, phân nhóm Lead nóng, theo dõi hành trình chuyển đổi đa nhãn hàng.
   - Cách ly tài sản thương hiệu bằng các file Markdown Brand Kit độc lập.

5. **Trung tâm Điều hành Kanban (Operations Hub)**:
   - Bảng điều phối tiến độ, giám sát luồng tác vụ và cảnh báo thời gian thực.

---

## Bản quyền & Phân phối (Licensing)

- Toàn bộ mã nguồn nền tảng Javis OS: Copyright (c) 2026 Nguyễn Minh Quý (blogminhquy), MIT License.
- Toàn bộ lớp mở rộng nghiệp vụ Sèo Trum: Copyright (c) 2026 Nhóm phát triển Sèo Trum (ROYCE-8425/Auto_social), MIT License.
- Xem chi tiết tại [LICENSE](LICENSE).
