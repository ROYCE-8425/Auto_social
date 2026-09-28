# Chăm sóc Fanpage (Fanpage Care): Bình luận, Messenger và CRM khách hàng

Tài liệu hướng dẫn sử dụng tính năng **Chăm sóc Fanpage** (Fanpage Care) trong Javis OS.

---

## 1. Giới thiệu tổng quan

Javis OS cung cấp khả năng đăng bài tự động đa kênh qua plugin `meta-pages-graph`. Tuy nhiên, phễu chuyển đổi và bán hàng chỉ thực sự diễn ra sau khi bài viết được đăng tải: học viên để lại bình luận hỏi học phí, lịch khai giảng, địa chỉ cơ sở, hoặc gửi tin nhắn vào hộp thư Messenger.

**Fanpage Care** là lớp chăm sóc khách hàng và bán hàng tự động đặt lên trên hạ tầng Fanpage hiện có:
1. **Hộp thư bình luận đa Trang**: Thu nạp toàn bộ bình luận (kể cả trả lời lồng), phân loại thông minh (rules-first, 0 token), tự động trả lời FAQ theo đúng cơ sở, ẩn spam và bắt lead SĐT.
2. **Hộp thư Messenger (Development & Live)**: Quản lý tin nhắn tập trung, tuân thủ cửa sổ 24 giờ của Meta, và kích hoạt cơ chế **Human Echo Takeover (4 giờ)** khi nhân viên trả lời trực tiếp từ Facebook.
3. **CRM Khách hàng trong Brain**: Tự động nhận diện danh tính (SĐT, PSID, Comment ID), tạo hồ sơ markdown trong `crm/customers/<crm_id>.md`, hỗ trợ gộp khách và tuân thủ Nghị định 13/2023/NĐ-CP (PDPD).
4. **An toàn tối đa**: Mặc định ở chế độ **`suggest`** (chỉ tạo bản nháp, không tự gửi ra ngoài), có công tắc khẩn cấp **Kill Switch**, và tự động im lặng trong khung giờ **21:00 - 07:00**.

---

## 2. Các nguyên tắc an toàn cốt lõi

### 2.1. CẤM bịa học phí và địa chỉ cơ sở
- **Địa chỉ**: Chỉ trích xuất đúng 1 địa chỉ cơ sở khớp với Fanpage hiện tại (`address_short`). Tuyệt đối không dán danh sách đa cơ sở chứa ký tự `|` hoặc nhầm lẫn giữa các chi nhánh (ví dụ: Trang Quận 7 không được trả lời địa chỉ Bình Dương). Nếu không xác định được cơ sở duy nhất, hệ thống sẽ đưa vào nháp (draft) cho nhân viên duyệt.
- **Học phí**: Chỉ báo học phí khi có số liệu cụ thể trong bảng giá file `wiki/courses/*.md` hoặc brand kit khớp với cơ sở. Nếu file chưa có số tiền, hệ thống sẽ sử dụng mẫu hotline tư vấn, **tuyệt đối không để AI tự bịa số tiền**.

### 2.2. Zero-token Preflight và Rules-First
- Để bảo vệ tài nguyên máy chủ (VPS 2 vCPU / 4 GB RAM), việc quét bình luận và phân loại hoàn toàn chạy bằng Python thuần:
  - Lọc spam theo regex / blocklist.
  - Bắt số điện thoại Việt Nam chuẩn hóa (10 số).
  - Khớp từ khóa FAQ cơ bản (học phí, địa chỉ, lịch học, khai giảng).
- Mô hình ngôn ngữ (LLM) chỉ được gọi qua `complete_json` (concurrency 1, timeout 20s, không mang theo công cụ đăng bài hay CLI) khi câu hỏi thuộc dạng kỹ thuật phức tạp hoặc mơ hồ ở chế độ `mode=full`.

### 2.3. Cửa sổ 24 giờ & Human Takeover (Messenger)
- **Cửa sổ 24 giờ**: Theo chính sách Meta, Page chỉ được gửi tin nhắn `RESPONSE` trong vòng 24 giờ kể từ tin nhắn gần nhất của người dùng. Ngoài 24 giờ, hệ thống ghi nhận `needs_human` và chuyển sang Kanban cho nhân viên.
- **Human Echo Takeover (4 giờ)**: Khi nhân viên trực tiếp chat với khách hàng trên ứng dụng Meta Business Suite hoặc Messenger native, Meta sẽ bắn webhook `message_echoes` (không mang metadata `care-worker`). Javis sẽ ngay lập tức **đóng băng tự động 4 giờ** đối với cuộc trò chuyện đó để tránh tình trạng bot và người cùng trả lời chồng chéo.
- **Nút "Javis nhận lại"**: Nhân viên có thể bấm nút trên dashboard bất kỳ lúc nào để Javis tiếp quản lại cuộc trò chuyện ngay lập tức.

---

## 3. Các chế độ vận hành (Modes)

| Chế độ | Mô tả | Hành vi |
|---|---|---|
| **suggest** *(Mặc định)* | An toàn nhất, dành cho giai đoạn làm quen | Chỉ phân loại, ghi nhận CRM và tạo bản nháp (draft). Nhân viên xem trên Dashboard và bấm **Gửi ngay** hoặc **Sửa rồi gửi**. Không gửi bất kỳ lệnh nào ra Facebook. |
| **auto** | Tự động trả lời mẫu chuẩn (Deterministic) | Tự động trả lời bình luận FAQ (địa chỉ, lịch học, học phí nếu có bảng) và gửi lời cảm ơn Lead để lại SĐT. Không gọi LLM, không gửi Messenger. |
| **full** | Tự động toàn diện có kiểm soát | Cho phép gọi AI grounded (`complete_json`) trả lời câu hỏi kỹ thuật/mơ hồ, gửi tin nhắn Messenger trong 24h, và tự động ẩn bình luận spam/toxic. |

---

## 4. Giao diện "Chăm sóc Fanpage" trên Dashboard

Truy cập menu bên trái: nhóm **Kết nối** > **Chăm sóc Fanpage**.

### Đầu trang (Controls & Status)
- **Công tắc bật/tắt Care**: Bật tính năng nhận diện và chăm sóc tự động.
- **Chọn chế độ**: `suggest` / `auto` / `full`.
- **Kill Switch**: Nút đỏ dừng khẩn cấp mọi tương tác gửi ra ngoài Facebook.
- **Chỉ báo giờ im lặng**: Biểu tượng trăng khuyết khi đang trong khung giờ 21:00 - 07:00 (chỉ tạo nháp, không gửi tin làm phiền khách ban đêm).
- **Quét ngay**: Kích hoạt tick quét bình luận tức thì.

### Ba tab chức năng chính
1. **Bình luận**:
   - Danh sách bản nháp (Drafts) đang chờ duyệt kèm nút **Gửi ngay**, **Bỏ qua**.
   - Hộp thư bình luận gần đây của tất cả các Trang, phân loại rõ ràng (Lead, FAQ, Khen, Kỹ thuật, Spam).
   - Nút **Tạo việc** để chuyển nhanh bình luận cần chăm sóc sang bảng Việc (Kanban).
2. **Messenger**:
   - Quản lý các cuộc hội thoại tin nhắn Page.
   - Hiển thị thời gian cửa sổ 24 giờ và trạng thái Human Takeover.
   - Nút **Javis nhận lại** để gỡ bỏ đóng băng khi nhân viên đã xong việc.
3. **Khách hàng (CRM)**:
   - Danh bạ khách hàng thu thập tự động từ bình luận và tin nhắn.
   - Tìm kiếm nhanh theo Tên hoặc Số điện thoại.
   - Xem hồ sơ chi tiết dạng Markdown trong Brain.
   - Nút **Gộp khách** khi một người tương tác từ nhiều tài khoản hoặc Fanpage khác nhau.
   - Nút **Xóa hồ sơ** tuân thủ Nghị định 13/2023/NĐ-CP (PDPD).
   - Checkbox **Sao lưu CRM lên GitHub** (mặc định bật).

---

## 5. Cấu hình hệ thống (`settings.json`)

```json
{
  "fanpage_care": {
    "enabled": false,
    "brain": "Brain Default",
    "mode": "suggest",
    "kill_switch": false,
    "quiet_hours": "21-07",
    "digest_enabled": true,
    "digest_hour": 20,
    "webhook_enabled": true,
    "backup_crm": true,
    "poll_interval_min": 5,
    "pages_per_tick": 10,
    "max_events_per_tick": 100,
    "max_new_customers_per_tick": 40,
    "takeover_hours": 4,
    "rate_limit": {
      "max_replies_per_page_per_hour": 8,
      "min_seconds_between_replies": 45
    },
    "hide_spam": false,
    "like_khen": false,
    "pages": {}
  }
}
```

---

## 6. Thiết lập Webhook Meta (Khuyến nghị cho Production)

1. Mở Facebook Developers Console > Chọn App của bạn > **Webhooks** > **Page**.
2. **Callback URL**: `https://<ten-mien-javis>/hook/facebook`.
3. **Verify Token**: Lấy token tạo ngẫu nhiên trong cài đặt Javis.
4. **Subscription Fields**: Đăng ký các trường sau:
   - `feed` (bình luận và trả lời bài viết).
   - `messages` (tin nhắn gửi đến).
   - `message_echoes` (tin nhắn nhân viên gửi từ Facebook native để kích hoạt Takeover).
5. Khi kết nối qua HTTPS, Javis sẽ nhận thông báo gần như tức thì mà không cần chờ chu kỳ quét (poller).
