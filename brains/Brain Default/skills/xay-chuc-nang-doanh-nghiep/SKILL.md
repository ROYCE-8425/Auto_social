---
name: Xây chức năng doanh nghiệp
description: "Biến yêu cầu nghiệp vụ công ty thành chức năng thật: phân tích, sửa code, kiểm thử và báo bằng chứng."
group: AI
---

# Xây chức năng doanh nghiệp

Skill này giúp Javis nhận một yêu cầu nghiệp vụ từ chủ doanh nghiệp hoặc ban giám khảo, rồi biến nó thành chức năng thật trong hệ thống Ops/AI Assistant: có phân tích, có code, có kiểm thử, có bằng chứng. Mục tiêu là chứng minh Javis không chỉ trả lời, mà có thể đồng hành như một nhân sự kỹ thuật hiểu quy trình công ty.

## Khi nào dùng

Dùng khi người dùng nói các câu như:

- "Javis build cho tôi chức năng ..."
- "Tạo nhanh màn/check/luồng để trình bày ban giám khảo"
- "Công ty tôi cần theo dõi ..."
- "Thêm chức năng phù hợp quy trình công ty"
- "Biến yêu cầu này thành UI/API/database thật"
- "Làm demo trực tiếp cho thấy AI có thể code chức năng mới"

Không dùng skill này cho việc viết bài Facebook, đăng TikTok, tra cứu wiki thông thường, hoặc chỉ trả lời tư vấn không cần sửa hệ thống.

## Chuẩn bị

1. Đọc `AGENTS.md` hoặc `CLAUDE.md` ở brain đang chọn để hiểu luật vault.
2. Đọc `Javis/index.md` để tránh tạo năng lực trùng.
3. Nếu yêu cầu liên quan vận hành công ty, đọc các memory/fact liên quan trong `memory/MEMORY.md`, đặc biệt:
   - `facts/ops_business_catalog.md` cho sản phẩm, bảng giá, mã SKU.
   - `facts/ops_documents_vault.md` cho tài liệu, hợp đồng, SOP.
   - `facts/ops_shipping_and_operations.md` cho đơn hàng, GHN, CSKH.
4. Rà code hiện tại trước khi sửa:
   - Backend FastAPI thường nằm ở `server/main.py` và module `server/ops_*.py`.
   - UI Ops React/Vite nằm ở `ops/src/pages`, `ops/src/components`, `ops/src/lib/api.ts`.
   - Route trong `/ops` và quyền RBAC phải kiểm tra qua `server/ops_rbac.py` hoặc guard trong `server/main.py`.
5. Nếu workspace bẩn, không revert thay đổi lạ. Chỉ chạm đúng file cần cho chức năng.

## Cách chạy

Nếu yêu cầu đủ rõ, làm luôn. Nếu thiếu điểm quyết định, hỏi đúng 1 câu ngắn. Ví dụ:

```text
Anh muốn chức năng này nằm trong màn Đơn hàng, Khách hàng hay AI Assistant?
```

Sau khi đủ thông tin, làm theo quy trình bên dưới. Không dừng ở plan nếu có thể triển khai ngay.

## Quy trình

### 1. Chốt ý nghĩa nghiệp vụ

Tóm tắt yêu cầu bằng 4 dòng:

```text
Mục tiêu: chức năng giúp ai làm việc gì.
Người dùng chính: chủ doanh nghiệp, quản lý, CSKH, sale, kho, kế toán.
Dữ liệu cần dùng: bảng/nguồn/API/tool hiện có.
Kết quả demo: khi bấm/chạy xong ban giám khảo thấy bằng chứng gì.
```

### 2. Chọn nơi tích hợp đúng

Ưu tiên gắn vào module có sẵn thay vì tạo màn giả:

- Đơn hàng, GHN, COD -> màn `Orders`, module `ops_orders`, `ops_order_store`, `ops_shipping`.
- Khách hàng, lead, inbox -> màn `Inbox` hoặc `Customers`, module `fanpage_care`, CRM store.
- Tài liệu, hợp đồng, SOP -> màn `Documents`, module `ops_documents`.
- Bảng giá, sản phẩm, khóa học -> màn `Products` hoặc catalog/settings.
- KPI, báo cáo điều hành -> dashboard/overview, không nhồi lại toàn bộ CRM hay Inbox.
- AI Assistant/OperationsHub -> chỉ dùng làm trung tâm lệnh, điều hướng, tự động hóa và giám sát; không clone lại module đã có.

Nếu chức năng chưa có dữ liệu thật, tạo dữ liệu mock có nhãn rõ `mock` hoặc `demo`, lưu qua store thật. Không hardcode UI để giả vờ có dữ liệu.

### 3. Thiết kế theo FACT -> SIGNAL -> ACTION

Mọi nhận định của AI phải tách tầng:

```text
FACT: dữ liệu thật hoặc mock đã ghi rõ nguồn.
SIGNAL: mẫu đáng chú ý rút từ FACT.
INFERENCE: giả thuyết, ghi rõ là suy luận.
ACTION: việc doanh nghiệp nên làm tiếp.
```

Không viết chắc như "phụ huynh đang..." hoặc "khách hàng chắc chắn..." nếu chỉ có vài nguồn nhỏ. Dùng "có thể", "tín hiệu cho thấy", "cần xác minh".

### 4. Lập patch nhỏ nhưng đủ luồng

Một chức năng trình bày tốt thường cần đủ 5 lớp:

1. Data model/store: bảng, file JSON, hoặc hàm CRUD thật.
2. Backend API: endpoint có auth/RBAC phù hợp.
3. Business logic: rule, trạng thái, audit log, so sánh hoặc sync.
4. Frontend UI/UX: nút, bảng, trạng thái, empty/error/loading.
5. Verification: test, build, seed demo, hoặc lệnh kiểm tra.

Nếu chạm route mới, cập nhật route snapshot/test nếu repo có yêu cầu.

### 5. Chuẩn UI/UX cho demo doanh nghiệp

- Giao diện phải giống công cụ vận hành: gọn, rõ trạng thái, dễ scan.
- Không dùng màn hero marketing cho chức năng nội bộ.
- Mỗi thao tác quan trọng cần có loading/disabled/toast hoặc trạng thái phản hồi.
- Với dữ liệu nhạy cảm, tránh phơi secret/token. Cho phép hiện mã đơn, trạng thái, số liệu nghiệp vụ cần thiết.
- Nếu là demo mock, gắn nhãn `Demo` hoặc `Mock` trong dữ liệu hoặc mô tả kỹ thuật, không đánh lừa là provider thật.
- Không tạo card rỗng "Coming soon" nếu người dùng yêu cầu chức năng phải chạy; chỉ dùng `Coming soon` cho phần ngoài phạm vi.

### 6. Kiểm thử và bằng chứng

Chạy kiểm tra phù hợp với phần đã sửa:

```powershell
python -m pytest <tests liên quan>
python tests/python/test_route_table.py
npm run build
```

Nếu có script seed/demo, chạy script và báo lại ID/mã/trạng thái tạo ra. Nếu không chạy được test nào, nói rõ lý do và rủi ro còn lại.

### 7. Báo cáo cuối để trình bày

Báo cáo ngắn theo mẫu:

```text
Đã build: <tên chức năng>
Ý nghĩa với công ty: <1-2 câu>
Luồng demo: <bước 1> -> <bước 2> -> <kết quả thấy được>
File chính đã sửa: <backend>, <frontend>, <test/seed>
Đã kiểm chứng: <lệnh pass>
Chưa làm: <nếu có, nói thật>
```

## Bẫy

- Không tạo chức năng trình diễn bằng dữ liệu hardcode trong React nếu chức năng cần vận hành thật.
- Không duplicate Inbox, CRM, KPI, Tasks, Calendar trong AI Assistant. AI Assistant nên điều phối và mở đúng module.
- Không tự bật hành động tiêu tiền, gửi tin, đăng bài, hủy đơn, đổi quảng cáo khi chưa có người duyệt.
- Không lưu token/API key vào repo, brain, wiki hoặc log.
- Không gọi provider thật khi chưa có cấu hình hoặc người dùng chưa cho phép. Với GHN, Meta, TikTok, Google Ads, dùng dry-run/mock rõ nhãn trước.
- Không nói "đã deploy/live" nếu mới build local. Tách rõ local test, VPS deploy, provider thật.
- Không sửa hàng loạt ngoài phạm vi demo, vì ban giám khảo cần thấy năng lực kiểm soát, không phải thay đổi hỗn loạn.

## Mẫu yêu cầu demo nên dùng

```text
Javis, dùng skill Xây chức năng doanh nghiệp.
Hãy tạo chức năng check trạng thái đơn GHN:
- tạo 2 đơn mock,
- có nút check trạng thái,
- cập nhật trạng thái đơn,
- chạy test và báo bằng chứng.
```

```text
Javis, công ty cần nơi lưu hợp đồng và SOP.
Hãy build Kho tài liệu có phân loại, ngày hết hạn, tìm kiếm và quyền truy cập nội bộ.
Làm đủ backend, UI và test tối thiểu.
```

```text
Javis, ban giám khảo hỏi hệ thống có tùy biến theo văn hóa công ty không.
Hãy thêm một chức năng nhỏ cho Sao Việt: theo dõi offer đối thủ theo FACT -> SIGNAL -> ACTION,
có seed dữ liệu demo và giao diện xem nhanh.
```

## Kiểm chứng skill

Sau khi tạo hoặc sửa skill này:

1. Kiểm tra description không quá 150 ký tự.
2. Kiểm tra frontmatter YAML hợp lệ.
3. Không cần sửa tay `Javis/index.md`; đó là chỉ mục tự sinh.
4. Nếu muốn ép Javis nhận ngay trong phiên đang chạy, khởi động lại hoặc chạy cơ chế sync/index của Javis nếu hệ thống có nút đồng bộ skill.
