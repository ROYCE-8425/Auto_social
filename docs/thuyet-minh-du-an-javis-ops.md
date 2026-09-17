# Thuyết minh / phân tích dự án  
## Javis Ops — Lớp vận hành mạng xã hội tự host cho SME

**Tên sản phẩm:** Javis Ops  
**Nền tảng:** Javis OS (mã nguồn mở, giấy phép MIT)  
**Repo:** Auto_social  
**Đối tượng thi:** Chuyển đổi số cho doanh nghiệp (SME)  
**Mô hình:** Tự host · mã nguồn mở · não AI phía sau · nhân viên chỉ thấy việc  

---

## 1. Bối cảnh và vấn đề

Doanh nghiệp nhỏ và vừa ở Việt Nam bán hàng và chăm sóc khách chủ yếu trên **Facebook Fanpage**, ngày càng thêm **Messenger** và **TikTok**. Thực tế vận hành thường gặp:

1. **Phân mảnh công cụ.** Đăng bài một chỗ (Creator Studio / điện thoại), trả lời comment chỗ khác, IB trong Business Suite, khách ghi Excel/Zalo. Không có một “ca làm việc” cho CSKH.
2. **Phụ thuộc người giỏi.** Chỉ một người biết đăng album, biết giọng brand, biết token. Nghỉ phép là page im.
3. **AI dùng sai chỗ.** Dán ChatGPT công khai dễ bịa giá, lẫn brand, lộ quy trình. Nhân viên không được cầm terminal hay API key.
4. **SaaS nước ngoài.** Buffer, ManyChat, Meta Business: thuê tháng, khóa dữ liệu, khó tùy theo ngành (shop game ≠ trung tâm đào tạo).
5. **Đa thương hiệu.** Một chủ có thể chạy nhiều page/ngành. Công cụ “một page một app” không scale.

**Nhu cầu chuyển đổi số:** không phải “có chatbot”. Là **số hóa quy trình đăng – chăm – ghi khách – phân quyền**, chạy trên máy doanh nghiệp, kiểm soát được.

---

## 2. Mục tiêu dự án

Xây **lớp vận hành (Ops)** đặt trên một hệ điều hành AI tự host:

| Mục tiêu | Ý nghĩa với DN |
|---|---|
| Não AI chạy nền | Đăng bài, đọc comment/IB, soạn nháp, bắt SĐT |
| Mặt trước cho người | CSKH duyệt, gửi, xem CRM — không đụng code |
| Phân quyền | Chủ / quản lý / nhân viên; nhân viên không vào terminal |
| Đa brand | Kit markdown: mỗi thương hiệu một giọng, một page, một kho ảnh |
| Tự chủ dữ liệu | Tự host, MIT, không khóa vendor |
| An toàn mặc định | Chỉ nháp; tự gửi Graph phải bật có chủ đích |

**Không nhằm:** thay Meta; làm mạng xã hội mới; chatbot “trả lời mọi câu”.

---

## 3. Giải pháp đề xuất

### 3.1 Định vị

**Javis Ops** = lớp chuyển đổi số cho kênh social của SME.  
**Javis OS** = bộ não (agent, skill, MCP, loop, wiki).  

Câu sản phẩm: *Não AI phía sau. Nhân viên chỉ thấy việc.*

### 3.2 Ba cửa (kiến trúc người dùng)

| Cửa | Đối tượng | Việc |
|---|---|---|
| `/` Landing | Công chúng, BTC | Kể chuyện sản phẩm |
| `/ops` | CSKH, quản lý | Hộp thư, CRM, việc, xem TikTok |
| `/app` | Chủ máy | Console Javis: kết nối, loop, Đăng thử, MCP |

Nhân viên **không** mở `/app` (máy chủ trả 403). Đó là điểm an toàn then chốt khi đưa AI vào DN.

### 3.3 Luồng nghiệp vụ (4 bước)

1. **Kết nối Fanpage** — Graph API chính chủ, Page Access Token; không lộ token ra dashboard nhân viên.  
2. **Javis đăng & đọc** — loop album theo brand kit; poll comment + hộp thư Business (Messenger). Phân loại **rules-first** (FAQ / lead / spam) để tiết kiệm token.  
3. **Nháp + CRM** — câu trả lời bám kit (cấm bịa giá). SĐT, page, brand ghi hồ sơ. Mặc định **không gửi** ra Facebook.  
4. **Người duyệt** — `/ops`: gửi comment hoặc gửi IB đúng kênh; giao việc Kanban khi cần người.

TikTok (tùy chọn): carousel 9:16 + nhạc gợi ý qua cổng PostPeer (DN tự có key). **Không** thay Graph cho Fanpage.

---

## 4. Tính mới so với cách làm cũ

| Tiêu chí | Cách cũ | Javis Ops |
|---|---|---|
| Đăng bài | Tay / tool thuê | Loop + kit + ảnh dataset/AI, Graph tự host |
| Comment / IB | Business Suite rời | Một `/ops`, tách **bình luận bài** và **tin nhắn IB** |
| Giọng brand | Nhớ trong đầu | Brand kit markdown, tách ngành (vd. shop game ≠ đào tạo) |
| Khách | Excel, tin nhắn rời | CRM từ tương tác; lọc theo brand/page |
| AI | ChatGPT dán tay | Soạn nháp; gửi Graph có công tắc và mode |
| Quyền | Chung mật khẩu page | RBAC staff / manager / owner |
| Chi phí nền | SaaS + nhân sự giỏi | VPS nhỏ + OSS; LLM chỉ khi cần |
| Minh bạch | Hộp đen | MIT, tự host, audit |

**Tính mở:** đứng trên Javis OS đã công bố MIT — không giấu nguồn. Phần đóng góp: Care, `/ops`, phạm vi đa brand, TikTok optional, RBAC.

---

## 5. Kiến trúc kỹ thuật (trình bày BTC)

```
Nhân viên  →  /ops (React)     →  REST Care / CRM / Kanban
Chủ máy    →  /app (Javis)     →  Engine + MCP + loop
Khách MXH  →  Facebook Graph / TikTok (PostPeer)
Dữ liệu    →  SQLite Care + vault markdown (kit, CRM, wiki)
```

- **Fanpage:** Meta Graph (đăng, comment, conversations, gửi tin).  
- **Phân loại:** Python, từ khóa + SĐT VN; pack theo brand.  
- **Gửi công khai:** chỉ khi mode ≠ “chỉ nháp” **và** công tắc tự trả lời bật.  
- **TikTok:** URL https công khai (`/tiktok-media`), `autoAddMusic`.  
- **Bí mật:** token/key trong state mã hóa, không git.

Phù hợp SME: một VPS 2 vCPU / 4 GB là mức tối thiểu đã khảo sát.

---

## 6. Phạm vi đã triển khai (nói đúng, không phóng)

**Đã có trên hệ thống:**

- Đăng Fanpage theo kit, nhiều page.  
- Care: kéo comment, kéo IB, nháp, gửi tay, takeover khi người trả lời.  
- Phạm vi: tất cả / theo nhóm brand / một page.  
- `/ops`: tổng quan, hộp thư, CRM, việc, xu hướng, TikTok (xem), nhân sự.  
- Landing công khai; buồng lái `/app`.  
- Plugin TikTok PostPeer; thư mục xuất 9:16.  
- Skill/loop/agent Facebook; skill TikTok (video) — agent/workflow carousel đang bổ sung.

**Đang hoàn thiện (nêu nếu giám khảo hỏi):** đồng bộ CRM theo brand từ event cũ; một lần đăng TikTok live từ nút Đăng thử; dán key PostPeer trên đúng VPS.

**Không làm trong phạm vi thi:** Instagram Ads, Zalo OA spam, crawler TikTok comment, khóa nguồn.

---

## 7. Lợi ích kinh tế — xã hội (góc chuyển đổi số)

- **Giảm thời gian** CSKH lật Business Suite + Excel.  
- **Giảm sai brand** (giá, ngành, hotline nhầm page).  
- **Giữ khách trong DN:** CRM trên máy mình, không thuê hộp thư AI nước ngoài.  
- **Nâng năng lực nhân sự phổ thông:** không cần biết Graph/API.  
- **Nhân rộng:** thêm page = thêm kit, không thêm app.  
- **Chi phí:** OSS + VPS; LLM tùy chọn.  
- **Lan tỏa:** MIT — DN khác fork, đổi kit thành ngành mình.

---

## 8. Rủi ro và kiểm soát

| Rủi ro | Kiểm soát |
|---|---|
| Bot trả lời sai / spam Graph | Mặc định nháp; rate limit; kill switch; giờ im lặng |
| Lộ token | Không hiện trên `/ops`; staff 403 `/app` |
| App Review Messenger | Page Token + poll; Development đủ demo |
| Vendor TikTok (PostPeer) | Optional; Fanpage không phụ thuộc |
| Bịa giá / lẫn brand | Kit + classifier tách pack; cấm bịa số không có trong file |
| Đạo văn OSS | NOTICE + LICENSE MIT, ghi công Javis OS |

---

## 9. Kế hoạch nhân rộng

1. **Ngay:** 1–2 Fanpage, mode nháp, CSKH duyệt.  
2. **Ổn định:** bật tự FAQ trên page tin cậy; CRM backfill.  
3. **Kênh phụ:** TikTok carousel khi đã Đăng thử live.  
4. **Ngành khác:** copy kit (F&B, spa, nội thất…) — không sửa não.  
5. **Cộng đồng:** README, CONTRIBUTING, không secret trên git.

---

## 10. Kết luận (chốt bài nói)

Javis Ops giải bài **vận hành social của SME**: AI làm việc nền, người làm việc khách, dữ liệu ở nhà, mã nguồn mở. Đó là chuyển đổi số **quy trình**, không phải gắn chatbot cho có.

**Câu chốt:** *Doanh nghiệp giữ quyền điều khiển. AI không ngồi ghế CSKH trừ khi chủ bật. Khách hàng không nói chuyện với terminal.*

---

## Phụ lục — Gợi ý slide (8–10 trang)

1. Vấn đề: page + IB + Excel  
2. Câu giải pháp + 3 cửa  
3. Demo luồng comment → nháp → gửi  
4. Tách IB ≠ comment  
5. Đa brand (kit)  
6. Phân quyền  
7. Tự host + MIT  
8. Kiến trúc 1 slide  
9. Rủi ro / công tắc an toàn  
10. Lộ trình + kêu gọi fork  

**Demo live:** `https://trannhuy.online/` (landing) → `/ops` (CSKH) → không đưa BTC vào `/app` trừ khi giải thích buồng lái.

**Trả lời sẵn “có phải copy Javis?”:** Có — não là Javis OS MIT, ghi công đủ. Phần thi là lớp Ops, Care, RBAC, đa brand. Minh bạch là điểm cộng.
