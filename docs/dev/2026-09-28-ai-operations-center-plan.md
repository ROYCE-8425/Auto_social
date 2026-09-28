# Plan: Javis Ops — AI Operations Center cho Doanh Nghiệp SME
> Ngày lập: 2026-09-28  
> Định vị: Chuyển dịch từ "Chatbot & Tool đăng bài" thành **Hệ điều hành vận hành thông minh (AI Operations Center)**.  
> Triết lý cốt lõi: **AI chủ động phát hiện việc -> Đề xuất phương án -> Thực thi an toàn -> Báo cáo & Học hỏi.**

---

## 1. TỔNG QUAN CHIẾN LƯỢC & TẦM NHÌN 2026

### 1.1. Bối cảnh & Vấn đề của SME Việt Nam
- Doanh nghiệp vừa và nhỏ (SME) và các trung tâm đào tạo / shop bán lẻ hiện nay bị phân mảnh nghiêm trọng:
  - Khách nhắn rải rác qua Facebook, Messenger, TikTok, Zalo.
  - Nhân viên trực page thường bỏ sót khách, không phân biệt được ai sắp mua và ai chỉ hỏi chơi.
  - Khách hỏi giá xong im lặng (drop-off) không ai chăm sóc lại.
  - Đăng bài chỉ biết đếm "view ảo" và "like", không biết bài nào sinh ra tiền thật (Content-to-Sale Attribution).
  - Chủ doanh nghiệp (Sếp) mù mờ về hiệu quả hàng ngày nếu không chủ động hỏi từng nhân viên.

### 1.2. Định vị Javis Ops (AI Operations Center)
Javis không đóng vai một "chatbot nói chuyện phiếm" hay "công cụ lên lịch đăng bài". Javis là **Trung tâm Điều phối Vận hành Doanh nghiệp**:
1. **Phát hiện (Detect):** Tự động bắt tín hiệu hội thoại, thời gian im lặng, nhu cầu khách hàng và xu hướng đối thủ.
2. **Quyết định (Score & Plan):** Chấm điểm tiềm năng mua hàng (Lead Score), sinh hành động tối ưu (Next Best Action), lập kế hoạch chiến dịch (Campaign Autopilot).
3. **Thực thi có kiểm soát (Action with Guardrails):** Ma trận 3 cấp độ an toàn (Human Approval Engine: Low - Medium - High).
4. **Báo cáo & Học hỏi (Attribution & Learning Loop):** Đo lường từ bài đăng đến doanh thu thực tế, tự học cấu trúc nội dung bán chạy và gửi báo cáo sáng sớm (Daily Briefing) cho Sếp.

---

## 2. BẢN ĐỒ 10 MODULE CỦA HỆ THỐNG

```
                             [ KHÁCH HÀNG ĐA KÊNH ]
                    (Facebook, Messenger, TikTok, Zalo, Web)
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │       JAVIS OMNICHANNEL INGESTION & MEMORY       │
             │       - Đồng bộ sự kiện đa kênh (Events)        │
             │       - Bảng nhận diện định danh (Identities)    │
             │       - Customer 360 Memory (Hồ sơ xuyên kênh)   │
             └────────────────────────┬─────────────────────────┘
                                      │
           ┌──────────────────────────┴──────────────────────────┐
           ▼                                                     ▼
┌─────────────────────────────┐                       ┌─────────────────────────────┐
│    AI LEAD SCORING &        │                       │    CONTENT ➔ SALE           │
│    NEXT BEST ACTION         │                       │    ATTRIBUTION & LEARNING   │
│ - Chấm điểm Hot/Warm/Cold   │                       │ - Post/Video ➔ Sale Matrix  │
│ - Thẻ hành động kế tiếp     │                       │ - Top conversion patterns   │
│ - Lost Lead Rescue (24h/3d) │                       │ - Competitor Radar          │
└──────────────┬──────────────┘                       └──────────────┬──────────────┘
               │                                                     │
               └──────────────────────────┬──────────────────────────┘
                                          ▼
                      ┌────────────────────────────────────────┐
                      │    HUMAN APPROVAL ENGINE (3 TẦNG)      │
                      │  🟢 Low Risk: Tự động (FAQ)            │
                      │  🟡 Medium: Nhân viên duyệt (Báo giá)   │
                      │  🔴 High: Quản lý duyệt (Hoàn tiền/CK) │
                      └───────────────────┬────────────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
      ┌───────────────────────────┐               ┌───────────────────────────┐
      │   AI DAILY BRIEFING       │               │   AI CAMPAIGN AUTOPILOT   │
      │ - 8h00 gửi Sếp (Telegram) │               │ - Nhập KPI mục tiêu       │
      │ - Executive Morning Hub   │               │ - Tự sinh 4-week pipeline │
      └───────────────────────────┘               └───────────────────────────┘
```

---

## 3. THIẾT KẾ KỸ THUẬT CHI TIẾT (TECHNICAL SPECIFICATIONS)

### Module 1: AI Daily Briefing (Bản tin sáng cho Sếp)
- **Backend:** 
  - File mới: `server/ops_briefing.py`
  - Endpoint: `GET /ops/briefing/today`
  - Thu thập chỉ số trong 24h từ `fanpage_care_store`:
    - Số hội thoại mới, số nháp đã duyệt, số phản hồi tự động.
    - Danh sách Hot Leads cần gọi chốt trong ngày.
    - Cảnh báo khách bị trễ > 6h hoặc khiếu nại chưa xử lý.
    - Bài viết có lượng tương tác / chuyển đổi cao nhất hôm qua.
  - Hỗ trợ gửi tự động qua Telegram/Zalo bot (`send_briefing_to_owner`).
- **Frontend ([Overview.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Overview.tsx)):**
  - Widget "Bản tin sáng nay của Javis": Gradient card hiện đại, 4 chỉ số vàng tóm tắt, danh sách việc ưu tiên của ngày, nút bấm "Bắn báo cáo qua Telegram/Zalo".

### Module 2: AI Lead Scoring (Chấm điểm độ nóng)
- **Backend:**
  - File mới: `server/lead_scoring.py`
  - Thuật toán chấm điểm theo ma trận hành vi:
    - Hỏi thông tin khóa học / sản phẩm: +15đ
    - Hỏi giá / học phí / phí dịch vụ: +20đ
    - Hỏi bảo hành / cam kết đầu ra / đổi trả: +15đ
    - Để lại Số điện thoại hợp lệ: +35đ
    - Hỏi số tài khoản / thanh toán / đặt cọc: +25đ
    - Tương tác sâu (số tin nhắn >= 4): +10đ
  - Xếp hạng:
    - `>= 70 điểm`: **HOT 🔥**
    - `40 - 69 điểm`: **WARM ⚡**
    - `< 40 điểm`: **COLD ❄️**
- **Frontend ([Inbox.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Inbox.tsx), [Tasks.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Tasks.tsx), [Customers.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Customers.tsx)):**
  - Hiển thị badge điểm nóng rõ ràng (Ví dụ: `85đ · Hot Lead 🔥`), phân loại bộ lọc tìm kiếm theo độ nóng, tự động ghim Hot Lead lên đầu hàng chờ.

### Module 3: Next Best Action (AI chỉ việc kế tiếp)
- **Backend:**
  - Tích hợp trong `server/lead_scoring.py` hoặc `server/ops_action_engine.py`:
  - Phân tích ngữ cảnh hội thoại và khoảng thời gian im lặng:
    - Khách Hot + im lặng > 2h ➔ Action: "Gọi điện chốt ưu đãi suất học thử miễn phí".
    - Khách đã nhận báo giá + im lặng > 6h ➔ Action: "Gửi mã voucher giảm 10% có hạn 2h".
    - Khách phàn nàn / tiêu cực ➔ Action: "Gắn nhãn Escalation - Chuyển quản lý ca giải quyết".
    - Khách chốt mua ➔ Action: "Gửi hướng dẫn thanh toán & lưu hồ sơ CRM".
- **Frontend ([Inbox.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Inbox.tsx)):**
  - Khung Action Card nổi bật ngay trên khung soạn thảo:
    - Hành động đề xuất + Lý do ("Vì khách đã hỏi giá 2 lần nhưng chưa chốt").
    - Nút thực hiện 1 chạm: "Dùng kịch bản này", "Bấm gọi ngay", "Tạo việc trên Kanban".

### Module 4: Customer Memory 360 (Nhớ khách xuyên kênh)
- **Backend:**
  - Tận dụng bảng `identities` và `customers` trong `server/fanpage_care_store.py`:
  - Ghép nối qua Số điện thoại (Global Key), PSID (Messenger), From ID (Comment Facebook), TikTok ID.
  - Endpoint: `GET /ops/customers/memory/{crm_id}` trả về toàn bộ dòng thời gian lịch sử tương tác đa kênh.
- **Frontend ([Inbox.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Inbox.tsx) & [Customers.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Customers.tsx)):**
  - Khối Customer 360 Timeline: Biểu thị các điểm chạm (Facebook Comment ➔ Messenger ➔ Zalo ➔ Gọi điện) để nhân viên nắm bắt toàn cảnh chân dung khách hàng.

### Module 5: AI Lost Lead Rescue (Phao cứu sinh Lead sắp mất)
- **Backend:**
  - Quét danh sách khách hàng `lead_hot` hoặc `interested` có `last_user_ts`:
    - `> 24h`: Tự sinh task "Chăm sóc lại khách nguội" trên Kanban.
    - `> 3 ngày`: Soạn sẵn kịch bản tái kích hoạt (Re-engagement Offer).
    - `> 7 ngày`: Đưa vào tệp Remarketing định kỳ.
- **Frontend ([Tasks.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Tasks.tsx)):**
  - Cột Kanban chuyên biệt "Cứu Lead sắp mất (Rescue)" với đồng hồ đếm ngược thời gian cơ hội chốt.

### Module 6: Content ➔ Sale Attribution (Doanh thu theo bài viết)
- **Backend:**
  - Endpoint `GET /ops/attribution/matrix`:
  - Khớp `events.object_id` (Post ID / TikTok Video ID) ➔ `from_id` (Khách) ➔ Giao dịch `purchased`.
  - Tính toán ROI: Lượt xem ➔ Lượt Inbox ➔ Số Lead tạo ra ➔ Đơn hàng hoàn tất ➔ Doanh thu (VND).
- **Frontend ([Trends.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Trends.tsx)):**
  - Bảng "Ma trận Chuyển đổi Doanh thu theo Nội dung" trực quan, có xếp hạng bài viết nào mang lại tiền thật cho doanh nghiệp.

### Module 7: AI Content Learning Loop (Vòng lặp tự học nội dung)
- **Backend:**
  - Trích xuất top 20% bài viết có tỷ lệ inbox/đơn cao nhất ➔ Phân tích đặc điểm thành công (Hook giật gân, CTA cụ thể, giá ưu đãi rõ ràng).
  - Tự động nạp các công thức này vào system prompt khi sinh kịch bản video hoặc bài đăng mới.
- **Frontend ([Trends.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Trends.tsx) & TikTok Studio):**
  - Thẻ thông báo "Công thức nội dung hiệu quả tuần này" (Ví dụ: "Caption dạng câu hỏi + khuyến mãi tạo ra inbox gấp 2.8 lần").

### Module 8: Competitor Radar (Rada đối thủ & Content Gap)
- **Backend:**
  - Quét dữ liệu công khai hoặc phân tích chủ đề đối thủ theo từ khóa ngành.
  - Phát hiện "Khoảng trống nội dung" (Content Gap): Chủ đề nào đối thủ chưa làm tốt mà khách hàng hay hỏi.
- **Frontend ([Trends.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/Trends.tsx)):**
  - Tab "Rada đối thủ": So sánh tần suất đăng bài, phân tích chủ đề đang thịnh hành và gợi ý cơ hội nội dung.

### Module 9: AI Campaign Autopilot (Điều phối chiến dịch theo mục tiêu)
- **Backend:**
  - Endpoint `POST /ops/campaigns/autopilot`: Nhận mục tiêu chiến dịch (ví dụ: "Tuyển 50 học viên MOS tháng 10").
  - AI sinh kế hoạch 4 giai đoạn (Tuần 1: Nhận thức ➔ Tuần 2: Giá trị/Giải pháp ➔ Tuần 3: Ưu đãi sớm ➔ Tuần 4: Đóng cổng).
  - Tự động sinh danh sách 12 tiêu đề bài viết + kịch bản video + kịch bản tư vấn tương ứng.
- **Frontend ([OperationsHub.tsx](file:///c:/Users/199X/OneDrive/Máy%20tính/Auto_social/Auto_social/ops/src/pages/OperationsHub.tsx)):**
  - Màn hình khởi tạo chiến dịch AI: Form nhập KPI trực quan ➔ Bấm nút "Kích hoạt Autopilot" ➔ Sinh toàn bộ lộ trình nhiệm vụ trên bảng điều hành.

### Module 10: Human Approval Engine (3 cấp độ kiểm soát rủi ro)
- **Backend:**
  - Mở rộng phân loại trong `server/fanpage_care_policy.py`:
    - `low`: FAQ công khai, thông tin cơ sở (Tự động duyệt 100%).
    - `medium`: Báo giá, gửi voucher <= 10%, tư vấn riêng (Nhân viên trực duyệt).
    - `high`: Hoàn tiền, ưu đãi > 20%, xử lý khiếu nại (Quản lý/Sếp duyệt).
- **Frontend:**
  - Huy hiệu phân cấp rõ ràng trên từng nháp: `[🟢 Tự động]`, `[🟡 Cần nhân viên duyệt]`, `[🔴 Cần Quản lý duyệt]`.

---

## 4. KẾ HOẠCH TRIỂN KHAI THEO GIAI ĐOẠN (ROADMAP)

### Giai đoạn 1: Lõi Vận Hành & Tác Động Tức Thì (Sprint 1)
- [x] Tạo tài liệu kiến trúc & kế hoạch tổng thể `docs/dev/2026-09-28-ai-operations-center-plan.md`.
- [ ] Xây dựng backend `server/lead_scoring.py` (Lead Scoring & Next Best Action logic).
- [ ] Xây dựng backend `server/ops_briefing.py` (AI Daily Briefing data generator).
- [ ] Tích hợp API vào `server/main.py`.
- [ ] Cập nhật giao diện `Overview.tsx` với Executive Daily Briefing Widget.
- [ ] Cập nhật `Inbox.tsx` với Lead Score badges, Next Best Action Card, và Human Approval Risk Level (🟢 Low / 🟡 Medium / 🔴 High).

### Giai đoạn 2: Trực Quan Hóa Doanh Số & Nhớ Khách Đa Kênh (Sprint 2)
- [ ] Mở rộng bảng `fanpage_care_store.py` hỗ trợ Content Attribution & Customer 360 Timeline.
- [ ] Cập nhật `Customers.tsx` hiển thị Customer 360 Omnichannel Memory (Facebook + TikTok + Zalo).
- [ ] Cập nhật `Tasks.tsx` (Kanban Board) hiển thị luồng Lost Lead Rescue và sắp xếp theo Lead Score.
- [ ] Cập nhật `Trends.tsx` với bảng Content ➔ Sale Attribution và Competitor Radar.

### Giai đoạn 3: Chiến Dịch Tự Động & Tối Ưu Hóa (Sprint 3)
- [ ] Xây dựng Campaign Autopilot generator trong `server/ops_campaign.py`.
- [ ] Bổ sung giao diện Campaign Autopilot trên `OperationsHub.tsx`.
- [ ] Kiểm thử toàn diện test suite (Backend Python tests + Frontend Vite build).
- [ ] Viết tài liệu tổng hợp thuyết trình đồ án / slide deck.
