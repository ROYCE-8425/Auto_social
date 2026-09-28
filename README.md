<div align="center">

# 🚀 SÈO TRUM (Auto Social AI)

**Nền tảng Tự động hóa Vận hành & Phân phối Nội dung Đa Kênh Cho Doanh Nghiệp SME. Đứng trên AI agentic đổi được bộ não Javis OS (MIT) - năng lực nằm ở Javis, không nằm ở model, hỗ trợ 11 nhà cung cấp.**  
*Mã nguồn mở (MIT License) · Tự host (Self-Hosted) · Bảo mật dữ liệu (Privacy-First)*

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)
[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](.github/workflows/ci.yml)

***Tiếng Việt** · [English](README.en.md)*

</div>

---

> [!NOTE]
> **Tuyên bố Nền tảng & Giấy phép MIT:**  
> Dự án **Sèo Trum** được phát triển trên nền tảng tác tử AI mã nguồn mở **[Javis OS](https://github.com/blogminhquy/javis-os)** (Bản quyền © 2026 Nguyễn Minh Quý - blogminhquy, giấy phép MIT).  
> Nhóm tác giả Sèo Trum kế thừa nhân xử lý tác tử và cổng kết nối công cụ (MCP Hub) của Javis OS, đồng thời thiết kế và phát triển mới hoàn toàn: **Hệ thống điều phối đa kênh (Social Channels Hub), Cổng xuất bản TikTok tự động, Hộp thư hợp nhất Human-in-the-Loop, CRM chấm điểm lead tự động và Cổng vận hành phân quyền RBAC (`/ops`)**.

---

## 🎯 Giới thiệu Dự án

Đối với các doanh nghiệp vừa và nhỏ (SME), mạng xã hội là huyết mạch kinh doanh nhưng cũng là gánh nặng vận hành lớn:
1. **Quá tải & Bỏ sót khách hàng:** Khách hàng phân mảnh trên 4–5 nền tảng (Facebook, TikTok, Instagram, YouTube). Trả lời chậm trễ sau 15–30 phút khiến tỷ lệ rớt đơn lên đến 60%.
2. **Rủi ro AI phát ngôn sai lệch:** Sử dụng chatbot tự do thả nổi (free-wheeling AI) dễ dẫn đến ảo giác (hallucination), tư vấn sai giá, cam kết sai chính sách gây khủng hoảng thương hiệu.
3. **Bẫy chi phí SaaS đóng:** Các nền tảng thương mại thu phí theo từng page, từng tài khoản nhân sự và khóa chặt dữ liệu khách hàng.

**SÈO TRUM** ra đời để giải quyết triệt để 3 bài toán trên bằng mô hình **Human-in-the-Loop**:
- **AI đảm nhận 80% tác vụ lặp lại:** Quét tin nhắn, bình luận 24/7; phân loại ý định khách hàng; tự động trích xuất số điện thoại; soạn sẵn bản nháp câu trả lời chuẩn xác theo Brand Kit thương hiệu chỉ trong 30 giây.
- **Con người nắm 20% quyền quyết định then chốt:** Nhân viên CSKH kiểm tra bản nháp và bấm "Duyệt gửi" 1-click. Tuyệt đối không để AI tự ý phát ngôn ra ngoài khi chưa được xác nhận.
- **1 Nội dung $\rightarrow$ 4 Kênh phân phối:** Biên tập một video ngắn hoặc album ảnh, tự động đẩy lên Facebook Reels, TikTok, Instagram và YouTube Shorts.

---

## 🚪 Mô hình 3 Cửa Truy cập (Three Portals)

Hệ thống phân tách rành mạch không gian trải nghiệm theo đúng vai trò người dùng:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          HỆ THỐNG SÈO TRUM                             │
├───────────────────┬──────────────────────────┬─────────────────────────┤
│    Cửa 1: `/`     │      Cửa 2: `/ops`       │       Cửa 3: `/app`     │
│   (Landing Page)  │     (Sèo Trum Ops)       │     (Buồng lái Lõi)     │
├───────────────────┼──────────────────────────┼─────────────────────────┤
│ Công chúng, khách │ Nhân viên CSKH (Staff),  │ Chủ máy (Owner),        │
│ ghé thăm tìm hiểu │ Quản lý vận hành (Mgr)   │ Kỹ sư vận hành hệ thống │
├───────────────────┼──────────────────────────┼─────────────────────────┤
│ Giới thiệu tính   │ Hộp thư duyệt nháp 30s,  │ Buồng lái AI, MCP Hub,  │
│ năng, bảng so     │ CRM & bắt số Lead nóng,  │ Second Brain Wiki, nạp  │
│ sánh, live demo   │ Social Hub, bảng Kanban  │ model AI, console máy   │
└───────────────────┴──────────────────────────┴─────────────────────────┘
```

| Cửa | Đường dẫn | Người dùng | Chức năng chính |
|---|---|---|---|
| **Trang chủ** | `/` | Khách truy cập, đối tác | Landing Page hiện đại giới thiệu tính năng, kiến trúc, bảng so sánh và bảng giá tự host |
| **Vận hành** | `/ops` | Nhân viên CSKH & Quản lý | Không gian làm việc hằng ngày: Duyệt nháp trả lời, quản lý khách hàng CRM, theo dõi lịch đăng đa kênh, bảng việc Kanban |
| **Buồng lái** | `/app` | Chủ máy (Owner) | Cấu hình bộ não AI, kết nối MCP, Second Brain Markdown, thanh điều hướng gom thành **7 nhóm** chức năng |

---

## ⚡ Tính năng Cốt lõi (Core Features)

### 1. Trung tâm Phân phối Đa Kênh (Social Channels Hub)
- Điều phối tập trung 4 nền tảng mạng xã hội: **Facebook Fanpage & Messenger**, **TikTok Video & Shop**, **Instagram & Threads**, **YouTube Shorts & Channel**.
- Ma trận phân phối 1:N: Tái sử dụng 1 video ngắn 9:16 hoặc bộ ảnh carousel để tiếp cận 95% tệp khách hàng tiềm năng mà không tốn công biên tập nhiều lần.

### 2. Hộp thư Hợp nhất & Duyệt Nháp 30 Giây (Unified Care Inbox)
- Gom bình luận Fanpage và tin nhắn Messenger vào một luồng duy nhất theo thời gian thực.
- **Bộ lọc ý định (Rules-First Intent Classifier):** Nhận diện chính xác khách hỏi giá, tư vấn cấu hình, hỏi địa chỉ, check inbox hay khiếu nại.
- **Trích xuất số điện thoại tự động:** Tự động bắt SĐT từ bình luận/tin nhắn (hỗ trợ đầy đủ các định dạng số Việt Nam: `09x`, `08x`, `+84`, có dấu chấm/cách/gạch ngang).
- **Phòng chống ảo giác (Anti-Hallucination):** AI chỉ soạn nháp dựa trên thông tin có sẵn trong Brand Kit. Nhân viên bấm 1-click "Duyệt gửi" hoặc chỉnh sửa nhanh trước khi gửi.

### 3. Khách hàng CRM & Chấm điểm Lead Tự động
- Tự động xây dựng hồ sơ khách hàng từ dữ liệu tương tác mạng xã hội.
- Phân loại trạng thái vòng đời khách hàng: *Khách mới $\rightarrow$ Đang tư vấn $\rightarrow$ Đã để lại SĐT (Lead nóng) $\rightarrow$ Đã mua hàng $\rightarrow$ Khiếu nại*.
- Hỗ trợ gộp trùng khách hàng (Merge Profiles) đa kênh và gắn thẻ tag phân nhóm.

### 4. Xuất bản TikTok Tự động (PostPeer BYO Gateway)
- Tích hợp cổng xuất bản video ngắn và album ảnh carousel qua PostPeer API (hỗ trợ Bring Your Own API Key).
- Tính năng tự động lồng nhạc nền hot trend (`autoAddMusic=True`).
- Máy chủ phục vụ CDN nội bộ `/tiktok-media` đáp ứng đúng tiêu chuẩn kỹ thuật kiểm duyệt của TikTok Content API.

### 5. Quản lý Đa Thương hiệu (Multi-Brand Kit Resolver)
- Quản lý thông tin từng thương hiệu bằng các file Markdown độc lập.
- Cô lập dữ liệu hoàn toàn: Giá cả, hotline, kịch bản chốt đơn của thương hiệu này không bao giờ bị rò rỉ sang thương hiệu khác.

### 6. Bảo mật & Phân quyền RBAC 3 Cấp
- 3 vai trò độc lập:
  * `staff`: Nhân viên trực ca CSKH  -  chỉ được xem hộp thư trong phạm vi phân công, duyệt nháp, tra cứu thông tin ca trực.
  * `manager`: Quản lý vận hành  -  xem báo cáo phân tích, gộp dữ liệu CRM, điều phối bảng việc Kanban.
  * `owner`: Chủ máy  -  toàn quyền quản trị tài khoản, cấu hình hệ thống và mở buồng lái `/app`.
- Máy chủ bảo vệ route nghiêm ngặt: Tự động từ chối bằng HTTP 403 fail-closed khi tài khoản không đủ quyền.

---

## 🏗️ Kiến trúc Hệ thống (System Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TẦNG KẾT NỐI (GATEWAY LAYER)                           │
│  Meta Graph API v20        PostPeer TikTok Gateway       YouTube Data API v3    │
│  (Fanpage & Messenger)     (Video 9:16 & Carousel)       (Shorts & Channel)     │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │ Webhooks & Polling Engine
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                    TẦNG LÕI XỬ LÝ & TÁC TỬ (CORE RUNTIME)                       │
│                                                                                 │
│  FastAPI Asynchronous Server ───┬─── SQLite WAL Queue (Chống nghẽn đơn)         │
│  Regex Phone Extractor          ├─── Rules-first Intent Classifier              │
│  Brand Kit Knowledge Resolver   └─── Human-in-the-Loop Draft Engine             │
│                                                                                 │
│  [Nhân Tác tử Agentic Kế thừa từ Javis OS (MIT) - Hỗ trợ 11 Nhà cung cấp AI]    │
│  Claude Code SDK · OpenAI Codex · Google Gemini · OpenRouter · DeepSeek         │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │ REST API & WebSocket Events
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                      TẦNG GIAO DIỆN (PRESENTATION LAYER)                        │
│                                                                                 │
│   Landing Page (`/`)         Sèo Trum Ops (`/ops`)         Buồng lái Lõi (`/app`)│
│   (HTML5 + Tailwind)         (React 18 + Tailwind SPA)     (Dashboard Quản trị) │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Cài đặt & Triển khai Nhanh (Deployment)

### Cách 1: Triển khai bằng Docker Compose (Khuyến nghị trên VPS)

```bash
# 1. Clone repository
git clone https://github.com/ROYCE-8425/Auto_social.git seotrum
cd seotrum

# 2. Tạo file cấu hình từ file mẫu
cp env.example .env

# 3. Khởi chạy toàn bộ hệ thống bằng Docker Compose
docker compose up -d

# 4. Kiểm tra trạng thái container
docker compose ps
```

Sau khi khởi chạy thành công:
- **Landing Page:** `http://<ip-vps>:7777/`
- **Sèo Trum Ops:** `http://<ip-vps>:7777/ops`
- **Buồng lái Chủ máy:** `http://<ip-vps>:7777/app`

---

### Cách 2: Triển khai Trực tiếp trên Linux / macOS (Native Systemd)

```bash
git clone https://github.com/ROYCE-8425/Auto_social.git seotrum
cd seotrum

chmod +x install.sh
./install.sh
```

Script sẽ tự động:
- Cài đặt Python 3.12, Node.js và môi trường ảo `venv`.
- Cài đặt các thư viện phụ thuộc (`requirements.txt`).
- Đăng ký dịch vụ `systemd` tự động khởi chạy cùng hệ điều hành.

---

### Cách 3: Chạy trên Windows (Máy tính Cá nhân)

1. Cài đặt **Python 3.12** (chọn *"Add Python to PATH"*) và **Node.js LTS**.
2. Chạy file: `setup.bat` (tự động cài môi trường).
3. Khởi động hệ thống: `JAVIS OS.bat` hoặc chạy nền bằng `start-javis.vbs` (tự chạy khi mở máy: `javis-autostart.bat`).
4. Mở trình duyệt truy cập: `http://localhost:7777/ops`.
5. Dừng hệ thống: chạy `stop-javis.bat`.

---

## ⚙️ Cấu hình Biến Môi trường (`.env`)

Sao chép `env.example` thành `.env` và điều chỉnh các thông số phù hợp:

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `JAVIS_HOST` | Địa chỉ lắng nghe (`127.0.0.1` nội bộ hoặc `0.0.0.0` công khai) | `127.0.0.1` |
| `JAVIS_PORT` | Cổng dịch vụ HTTP | `7777` |
| `JAVIS_REQUIRE_LOGIN` | Bắt buộc đăng nhập tài khoản | `1` |
| `JAVIS_ADMIN_USER` | Tên tài khoản quản trị tối cao (Owner) | *(tự đặt)* |
| `JAVIS_ADMIN_PASSWORD` | Mật khẩu tài khoản quản trị tối cao | *(tự đặt)* |
| `DOMAIN_NAME` | Tên miền trỏ về máy chủ (tự cấp chứng chỉ SSL) | *(tùy chọn)* |
| `POSTPEER_API_KEY` | Khóa API PostPeer cho xuất bản TikTok Gateway | *(tùy chọn)* |
| `POSTPEER_TIKTOK_ACCOUNT_ID` | Mã định danh tài khoản TikTok kết nối | *(tùy chọn)* |
| `BRAINS_DIR` | Thư mục lưu trữ Second Brain và Brand Kit Markdown | `brains/` |

---

## 🔒 An toàn & Bảo mật Dữ liệu

- **Không rò rỉ khóa bí mật:** Toàn bộ token Facebook, API key PostPeer và biến môi trường nhạy cảm đều được lưu trong vault an toàn, không bao giờ commit vào Git.
- **Phòng chống tấn công Web:** Mặc định tích hợp bộ lọc chống tấn công CSRF, DNS-rebinding và giới hạn tần suất đăng nhập (Rate-limiting).
- **Fail-Closed RBAC:** Tất cả các endpoint nghiệp vụ `/ops/*` đều bắt buộc xác thực phiên và kiểm tra quyền hạn trước khi trả dữ liệu.

---

## 🧪 Kiểm thử Tự động (Automated Testing)

Hệ thống được bảo vệ bởi bộ kiểm thử tự động toàn diện chạy trên GitHub Actions CI:

```bash
# Kiểm thử toàn bộ endpoint và phân quyền backend
python -m pytest tests/python -k "not test_browser"

# Kiểm thử route độc lập
python tests/python/test_ops_routes.py
python tests/python/test_ops_rbac.py
python tests/python/test_landing.py

# Build kiểm tra giao diện Ops Dashboard
cd ops && npm run build
```

---

## 📜 Bản quyền & Ghi công (Attribution & License)

Dự án phát hành dưới giấy phép mã nguồn mở **MIT License**:

- **Nền tảng Tác tử Lõi (Core Agentic Engine & MCP Hub):**  
  Kế thừa từ dự án [Javis OS](https://github.com/blogminhquy/javis-os)  
  Copyright (c) 2026 Nguyễn Minh Quý (blogminhquy)

- **Lớp Nghiệp vụ & Vận hành Sèo Trum (Social Hub, TikTok Automation, Fanpage Care CRM, Ops RBAC Portal):**  
  Copyright (c) 2026 Nhóm phát triển Sèo Trum (`ROYCE-8425/Auto_social`)

Xem chi tiết điều khoản cấp phép tại [LICENSE](LICENSE) và [NOTICE.md](NOTICE.md).

---

<div align="center">

**SÈO TRUM  -  Đồng hành cùng doanh nghiệp SME làm chủ kỷ nguyên tự động hóa AI.**  
Mọi đóng góp, báo lỗi (issue) và Pull Request đều được hoan nghênh trên [GitHub Repository](https://github.com/ROYCE-8425/Auto_social).

</div>
