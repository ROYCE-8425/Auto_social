# Kế hoạch biến Sèo Trum Ops thành ứng dụng vận hành thật

Ngày lập: 2026-09-28

## 1. Chẩn đoán hiện trạng

Repo hiện tại có hai lớp khác nhau:

- Lớp nền Javis OS đã có nhiều đường chạy thật: auth, MCP, brain, workflow, Kanban, file manager, Telegram/Zalo, Graph connector, PostPeer TikTok.
- Lớp Sèo Trum Ops đang có UI đẹp nhưng nhiều module còn là demo/mock, đặc biệt ở `/ops#hub`, `/ops#customers`, `/ops#inbox`, `/ops#trends`, một phần `/ops#overview`.

Các mock lớn đã thấy:

- `ops/src/pages/OperationsHub.tsx`: `modulesData` hardcode toàn bộ phân hệ, record, confidence, trạng thái AI.
- `ops/src/pages/Customers.tsx`: `mockCustomersList`, nhiều nút chỉ `alert(...)`.
- `ops/src/pages/Inbox.tsx`: `mockConversationsData`, state hội thoại local, một số thao tác chỉ alert/prompt.
- `ops/src/pages/Tasks.tsx`: có gọi Kanban thật nhưng vẫn còn dữ liệu/trải nghiệm mock.
- `ops/src/pages/Overview.tsx`: trộn số liệu thật với fallback mock chart/table.
- `ops/src/pages/Trends.tsx`: gọi API thật nhưng backend attribution/competitor đang trả dữ liệu mẫu.
- `server/ops_briefing.py`: lấy một ít `fanpage_care_store.get_stats()` nhưng hot leads, top post, alerts vẫn hardcode.
- `server/ops_attribution.py`: ma trận bài viết, insights, competitor radar hardcode.
- `server/ops_campaign.py`: tạo kế hoạch chiến dịch tĩnh, không persist, không tạo task, không tạo draft thật.

Điểm mạnh không nên viết lại:

- `fanpage_care.py` và `fanpage_care_store.py` đã có store SQLite, event, draft, conversation, CRM, send/reject draft, poll Graph, release takeover.
- `tasks.py` và `task_store.py` đã có Kanban thật.
- `tiktok_service.py` đã có PostPeer, crop ảnh 9:16, log bài gần đây, loop status.
- `/ops/users` và RBAC đã có khung vận hành, nhưng cần siết production.

Rủi ro nghiêm trọng cần sửa sớm:

- `server/main.py` endpoint `/ops/me` đang tự cấp session `owner` nếu không có user. Đây có thể tiện demo nhưng không phù hợp production/public. Cần chỉ bật auto-owner trong dev/demo explicit flag, còn production phải trả 401.
- Không được tiếp tục thêm module “AI tự động” nếu chưa có action thật hoặc hàng đợi duyệt thật. UI phải phân biệt rõ `Dữ liệu thật`, `Chưa kết nối`, `Demo seed`.

## 2. Định nghĩa sản phẩm thật cho MVP

MVP thực tế không nên ôm hết HR, hợp đồng, tài chính, LMS ngay. Nên chốt phạm vi thật trong 4 trụ:

1. **Hộp thư & Nháp thật**
   - Nguồn: Facebook comments, Messenger conversations từ `fanpage_care_store`.
   - Hành động thật: gửi nháp, từ chối nháp, nhắn trực tiếp trong cửa sổ 24h, release takeover, tạo việc Kanban.
   - Empty state thật khi chưa kết nối Facebook hoặc chưa có dữ liệu.

2. **CRM & Lead Scoring thật**
   - Nguồn: customers/events/identities trong `fanpage_care_store`.
   - Hành động thật: xem hồ sơ, backfill từ events, merge/delete theo quyền, tạo task follow-up, gắn tag nếu có store.
   - Lead score tính từ lịch sử message/comment thật, số điện thoại, intent, thời gian im lặng.

3. **Điều hành chiến dịch thật**
   - Campaign Autopilot phải persist vào DB/file state.
   - Khi tạo campaign: sinh milestones, content items, objection playbook, review checklist, đồng thời tạo Kanban tasks hoặc campaign tasks.
   - Không chỉ trả JSON hiển thị rồi mất.

4. **Social publishing thật**
   - TikTok: dùng PostPeer hiện có.
   - Facebook: dùng Graph connector hiện có qua `fanpage_care_graph`/MCP tool tương ứng.
   - Instagram/Youtube/Zalo: nếu chưa có connector thật thì hiển thị `Chưa kết nối`, không giả lập đã đăng.

Các module HR, hợp đồng, tài chính, dự án chỉ nên là **Knowledge Modules** ở MVP:

- Có hồ sơ/tài liệu/SOP thật trong brain.
- Có search/list thật.
- Chưa tuyên bố “AI tự động ký hợp đồng, đối soát ngân hàng” nếu chưa có integration.

## 3. Roadmap triển khai

### Phase 0 - Production guardrails

Mục tiêu: chặn demo behavior nguy hiểm và chuẩn hóa trạng thái mock.

Việc cần làm:

- Sửa `/ops/me`: không tự tạo owner session khi production login required. Có thể cho phép auto-owner chỉ khi `JAVIS_OPS_DEMO_AUTO_OWNER=1` hoặc `JAVIS_REQUIRE_LOGIN=0`.
- Thêm cờ response `data_source`: `real | empty | demo_seed | disconnected`.
- Thêm helper frontend hiển thị badge `Dữ liệu thật`, `Chưa kết nối`, `Demo`.
- Test RBAC: unauthenticated `/ops/me` phải 401 trong production mode.

Files chính:

- `server/main.py`
- `server/ops_rbac.py`
- `ops/src/lib/auth.tsx`
- `ops/src/components/*`
- `tests/python/test_ops_rbac.py`

### Phase 1 - Xóa mock UI ở các màn hình lõi

Mục tiêu: `/ops` không dùng mảng mock cho những nghiệp vụ đã có API thật.

Việc cần làm:

- `Inbox.tsx`: dùng `api.getInbox`, `api.getConversations`, `api.getConversationThread`, `api.sendDraft`, `api.rejectDraft`, `api.sendDirectMessage`, `api.releaseTakeover`, `api.handoffToStaff`.
- `Customers.tsx`: bỏ `mockCustomersList`; dùng `api.getCustomers`, `api.getCustomerDetail`, `api.backfillCustomers`, `api.mergeCustomers`, `api.deleteCustomer`.
- `Tasks.tsx`: chỉ dùng Kanban API thật; các nút thêm/move/delete gọi API, không alert.
- `Overview.tsx`: chart/table lấy từ `getCareState`, `getInbox`, `getCustomers`, `getTasks`, `getDailyBriefing`; nếu không có data thì empty state.
- `OperationsHub.tsx`: bỏ `modulesData` hardcode hoặc chuyển thành metadata tĩnh, còn counts/records lấy từ API mới.

Tiêu chí hoàn thành:

- Search `mockCustomersList`, `mockConversationsData`, `modulesData` không còn là nguồn dữ liệu nghiệp vụ.
- Search `alert(` trong pages lõi không còn cho thao tác nghiệp vụ.
- UI không hiển thị tên khách/số tiền/sample post khi backend không có dữ liệu.

Files chính:

- `ops/src/pages/Inbox.tsx`
- `ops/src/pages/Customers.tsx`
- `ops/src/pages/Tasks.tsx`
- `ops/src/pages/Overview.tsx`
- `ops/src/pages/OperationsHub.tsx`
- `ops/src/lib/api.ts`

### Phase 2 - Backend Ops Insights thật

Mục tiêu: các endpoint `/ops/briefing`, `/ops/attribution`, `/ops/lead-scoring` trả dữ liệu từ store thật.

Việc cần làm:

- `ops_briefing.py`:
  - Hot leads lấy từ `search_customers` + `customer_behavior` + `lead_scoring.evaluate_lead_score`.
  - Alerts lấy từ pending drafts, conversations unreplied, takeover quá hạn, quiet hours, disconnected connectors.
  - Top post chỉ trả khi có dữ liệu log publishing/attribution thật; nếu chưa có thì `top_post: null`.
- `ops_attribution.py`:
  - Tạo store thật cho content posts và attribution events.
  - Phase đầu có thể lấy recent TikTok posts từ `tiktok_service.get_recent_posts` và inbox events liên quan CTA/UTM nếu có.
  - Không hardcode `post_101`.
- `lead_scoring.py`:
  - Cho endpoint nhận `crm_id`, server tự lấy message history thay vì frontend tự gửi messages mock.
  - Trả risk/action có citation tới customer/event.

Schema gợi ý:

- `ops_campaigns`: id, goal, status, owner_id, scope_brand, scope_page_id, budget_vnd, target_revenue_vnd, created_at, updated_at.
- `ops_campaign_items`: id, campaign_id, platform, scheduled_day, hook, cta, status, draft_ref, post_id, metrics_json.
- `ops_content_posts`: id, platform, external_post_id, title, caption, published_at, campaign_id, urls_json, metrics_json.
- `ops_attribution_events`: id, source_post_id, event_id, crm_id, event_type, value_vnd, created_ts.

Files chính:

- `server/ops_briefing.py`
- `server/ops_attribution.py`
- `server/lead_scoring.py`
- `server/fanpage_care_store.py`
- `server/tiktok_service.py`
- `tests/python/test_ops_real_data.py`

### Phase 3 - Campaign Autopilot thành workflow thật

Mục tiêu: bấm “Khởi tạo chiến dịch với AI” tạo campaign thật, tasks thật, content calendar thật.

Luồng sản phẩm:

1. Owner nhập mục tiêu, ngân sách, thời gian, kênh, scope brand/page.
2. Backend sinh plan bằng rules + optional LLM, validate schema.
3. Persist campaign + items.
4. Tạo Kanban tasks:
   - Viết hook/content
   - Chuẩn bị media
   - Duyệt nội dung
   - Đăng Facebook/TikTok
   - Theo dõi lead và báo cáo
5. UI hiển thị campaign detail: calendar, tasks, post status, lead attribution.

Không được làm:

- Không chỉ `return generate_campaign_autopilot(...)` rồi mất state.
- Không đánh dấu đã đăng nếu chưa có `post_id` thật từ Graph/PostPeer.
- Không tự bịa doanh thu.

Files chính:

- `server/ops_campaign.py`
- `server/main.py` endpoints `/ops/campaigns/*`
- `server/task_store.py` hoặc `tasks_feature.enqueue`
- `ops/src/pages/OperationsHub.tsx`
- `ops/src/lib/api.ts`
- `tests/python/test_ops_campaigns.py`

### Phase 4 - Social Channels thật

Mục tiêu: “Đa kênh Social” phản ánh trạng thái connector thật, không giả lập.

Việc cần làm:

- TikTok: giữ PostPeer flow hiện có, bổ sung status rõ: connected, account, recent posts, failed reason.
- Facebook: dùng Facebook Pages connector; hiển thị page list, permissions, last poll, post ability.
- Zalo/Instagram/Youtube: nếu chưa có tool thật thì chỉ hiển thị backlog/coming soon, không có số liệu giả.
- Mọi publish action phải có idempotency key, lưu `post_id`/external id, log kết quả.

Files chính:

- `ops/src/pages/SocialChannels.tsx`
- `server/tiktok_service.py`
- `server/fanpage_care_graph.py`
- `server/mcp_store.py`
- `server/tasks.py`

### Phase 5 - QA, demo thật, contest packaging

Mục tiêu: bài dự thi chứng minh chạy thật.

Checklist:

- Demo data seed tách riêng: `scripts/seed_demo_ops.py`, không lẫn production.
- Toggle demo rõ ràng: `JAVIS_DEMO_SEED=1`.
- Video demo phải cho thấy:
  - Kết nối Facebook/PostPeer thật hoặc trạng thái chưa kết nối thật.
  - Poll comment/message thành event thật.
  - AI tạo draft, nhân viên duyệt gửi.
  - CRM tạo/update từ event thật.
  - Campaign tạo task thật.
- Test:
  - `python tests/run.py --py`
  - `pytest tests/python/test_ops_rbac.py tests/python/test_fanpage_care_*.py tests/python/test_ops_campaigns.py`
  - `cd ops && npm run build`

## 4. Quy tắc quản lý dự án khi giao Gemini Code

Không giao kiểu “làm hết app thành thật”. Phải chia prompt nhỏ, có files, đầu ra, test, và cấm mock.

Luật bắt buộc trong mọi prompt:

- Không thêm dữ liệu mẫu hardcode mới.
- Không dùng `alert()` cho nghiệp vụ thật.
- Không bypass RBAC.
- Không tự bịa Graph/PostPeer success.
- Nếu integration chưa có, trả `disconnected` hoặc empty state.
- Không sửa unrelated files.
- Luôn thêm/cập nhật test cho behavior server.

## 5. Prompt 1 cho Gemini Code - Production guardrails + data source badges

```text
Bạn đang làm trong repo Auto_social. Mục tiêu: biến /ops từ demo sang production-safe bước đầu, không thêm tính năng mới.

Files cần đọc trước:
- server/main.py đoạn /ops/me, /ops auth, AI Operations endpoints
- server/ops_rbac.py
- ops/src/lib/auth.tsx
- ops/src/lib/api.ts
- ops/src/App.tsx
- tests/python/test_ops_rbac.py

Yêu cầu:
1. Sửa endpoint GET /ops/me:
   - Không được tự cấp owner session khi không có user trong production.
   - Chỉ cho auto-owner nếu biến env JAVIS_OPS_DEMO_AUTO_OWNER=1 hoặc JAVIS_REQUIRE_LOGIN=0.
   - Khi không có user và không ở demo mode: trả 401 JSON { "user": null, "error": "unauthorized" }.
2. Frontend AuthProvider phải xử lý 401 bằng user=null, không crash.
3. Thêm helper/type data_source nếu cần nhưng chưa phải redesign UI.
4. Không đổi luồng login hiện có.
5. Không thêm mock data.

Test bắt buộc:
- Thêm hoặc sửa tests/python/test_ops_rbac.py để cover:
  a) /ops/me unauthenticated production returns 401
  b) /ops/me demo auto owner only when env flag enabled
  c) owner session still works
- Chạy pytest file liên quan.

Tiêu chí done:
- git diff không chứa secret/runtime files.
- Không sửa README/NOTICE trong task này.
```

## 6. Prompt 2 cho Gemini Code - Replace Inbox/Customers mock with real API

```text
Bạn đang làm trong repo Auto_social. Mục tiêu: /ops#inbox và /ops#customers dùng dữ liệu thật từ Fanpage Care store/API, không dùng mock arrays.

Files cần đọc trước:
- ops/src/pages/Inbox.tsx
- ops/src/pages/Customers.tsx
- ops/src/lib/api.ts
- server/fanpage_care.py routes /fanpage-care/inbox, /drafts, /customers, /conversations
- server/fanpage_care_store.py list_events/list_drafts/search_customers/customer_behavior

Yêu cầu Inbox:
1. Xóa nguồn dữ liệu nghiệp vụ mockConversationsData khỏi render chính.
2. Dùng:
   - api.getInbox({ limit, kind, brand/page scope })
   - api.getConversations(...)
   - api.getConversationThread(pageId, psid)
   - api.sendDraft(draftId), api.rejectDraft(draftId)
   - api.sendDirectMessage(pageId, psid, message)
   - api.releaseTakeover(pageId, psid)
   - api.handoffToStaff(...)
3. Nếu chưa có dữ liệu, hiển thị empty state: "Chưa có hội thoại/nháp. Hãy kết nối Facebook Pages hoặc bấm Quét ngay."
4. Không dùng alert() cho thao tác nghiệp vụ; hiển thị inline toast/status text.

Yêu cầu Customers:
1. Xóa mockCustomersList khỏi render chính.
2. Dùng api.getCustomers(), api.getCustomerDetail(), api.backfillCustomers(), api.mergeCustomers(), api.deleteCustomer().
3. Nút gọi/chat/task/tag nếu chưa có backend thật thì disable hoặc mở đúng luồng hiện có, không alert giả thành công.
4. SĐT theo quyền: giữ backend masking nếu có; frontend không tự lộ dữ liệu.

Test/verify:
- cd ops && npm run build
- Nếu sửa API contract backend, thêm pytest tương ứng.

Tiêu chí done:
- rg "mockCustomersList|mockConversationsData|alert\\(" ops/src/pages/Inbox.tsx ops/src/pages/Customers.tsx không còn match cho nghiệp vụ chính.
- UI vẫn build.
```

## 7. Prompt 3 cho Gemini Code - Real briefing and attribution

```text
Bạn đang làm trong repo Auto_social. Mục tiêu: /ops/briefing và /ops/attribution không trả dữ liệu hardcode nữa.

Files cần đọc trước:
- server/ops_briefing.py
- server/ops_attribution.py
- server/lead_scoring.py
- server/fanpage_care_store.py
- server/tiktok_service.py
- server/main.py endpoints /ops/briefing/*, /ops/attribution/*
- ops/src/pages/Overview.tsx
- ops/src/pages/Trends.tsx

Yêu cầu:
1. ops_briefing.get_daily_briefing:
   - Lấy stats thật từ fanpage_care_store.get_stats().
   - Tạo hot_leads từ customers/events thật: dùng search_customers + customer_behavior + lead_scoring.
   - Nếu không có customer thật, hot_leads=[]; không dùng tên/số điện thoại mẫu.
   - top_post chỉ có khi có recent post/log thật; không hardcode bài Excel.
   - alerts sinh từ pending drafts, unreplied conversations, connector disconnected, hoặc empty.
2. ops_attribution:
   - Xóa danh sách post_101..post_105 hardcode.
   - Tạm thời tổng hợp từ tiktok_service.get_recent_posts và event/draft counts nếu chưa có bảng attribution.
   - Thêm data_source: real | empty | partial.
   - competitor radar nếu chưa có crawler thật thì trả disconnected/not_configured, không bịa tên đối thủ.
3. Frontend Overview/Trends phải render empty/partial states, không fallback sang mock.

Test bắt buộc:
- Thêm tests/python/test_ops_briefing_real_data.py:
  a) empty store không trả tên khách mẫu
  b) stats thật được phản ánh vào kpis
  c) attribution empty không có post_101
- Chạy pytest file mới.

Tiêu chí done:
- rg "lead_1|post_101|Trung tâm Tin học X|Nguyễn Thị Hoa|Phím tắt Excel" server/ops_briefing.py server/ops_attribution.py không còn match dữ liệu hardcode.
```

## 8. Prompt 4 cho Gemini Code - Persist Campaign Autopilot and create Kanban tasks

```text
Bạn đang làm trong repo Auto_social. Mục tiêu: Campaign Autopilot tạo chiến dịch thật có lưu state và task thật, không chỉ trả plan tĩnh.

Files cần đọc trước:
- server/ops_campaign.py
- server/main.py endpoint /ops/campaigns/autopilot
- server/tasks.py và server/task_store.py
- ops/src/pages/OperationsHub.tsx
- ops/src/lib/api.ts

Thiết kế:
1. Tạo store nhẹ cho campaign, ưu tiên SQLite trong STATE_DIR:
   - ops_campaigns
   - ops_campaign_items
2. POST /ops/campaigns/autopilot:
   - Validate input goal, budget, duration, platforms.
   - Generate plan.
   - Persist campaign + items.
   - Enqueue Kanban tasks cho các bước review/content/publish/follow-up.
   - Trả campaign_id, campaign_plan, task_ids.
3. Thêm GET /ops/campaigns và GET /ops/campaigns/{id}.
4. OperationsHub:
   - Load campaigns thật.
   - Sau khi tạo, hiển thị campaign_id, task_ids, status.
   - Không hiển thị "đã đăng" nếu chưa có external post_id.

Ràng buộc:
- Không gọi publish thật trong task này.
- Không bịa doanh thu/post_id.
- Nếu Kanban enqueue fail phải trả error rõ, không báo thành công.

Test bắt buộc:
- tests/python/test_ops_campaigns.py:
  a) tạo campaign persist được
  b) tạo campaign sinh task ids
  c) get campaign trả đúng items
- cd ops && npm run build
```

## 9. Vai trò PM khi review kết quả Gemini

Sau mỗi prompt, người quản lý dự án phải kiểm:

- `git diff` có sửa đúng files không.
- Không xuất hiện mock mới bằng:
  - `rg -n "mock|sample|fake|alert\\(|post_101|lead_1|Nguyễn Thị Hoa" ops/src server/ops_*.py server/lead_scoring.py`
- API có phân biệt empty/disconnected thật không.
- Build/test có chạy thật không.
- UI không claim hành động đã hoàn tất nếu backend chưa có action thật.

Ưu tiên merge:

1. Guardrails auth/RBAC.
2. Inbox/Customers thật.
3. Briefing/Attribution thật.
4. Campaign persistence + Kanban.
5. Social publishing expansion.

