# Plan: Dashboard vận hành (mặt trước) — Javis là bộ não ẩn phía sau

| Trường | Giá trị |
| --- | --- |
| **Cho** | Gemini implement |
| **Ngày** | 2026-09-16 |
| **Khách dùng** | Nhân viên CSKH / tư vấn + Quản lý trung tâm Sao Việt |
| **Không phải** | Viết lại console Javis hiện tại (`dashboard/console.js`) |
| **Nguyên tắc** | Mặt sau (engine, MCP, Care policy, loop, brain) **không sửa**. Mặt trước SPA mới đọc API đã có. |

Javis OS hôm nay là **buồng lái chủ máy**: chat, terminal, MCP, model, 19 trang. Nhân viên không được vào đó. Cần một **dashboard vận hành** riêng: đẹp, production, chỉ việc bán hàng / chăm sóc — hiện những gì Javis đã làm, khách, xu hướng, việc cần người.

---

## 0. Quyết định kiến trúc (bắt buộc đọc)

```
Nhân viên/QL  →  /ops  (SPA React)  →  REST Javis đã có
Chủ máy       →  /     (console Alpine hiện tại, nguyên si)
Bộ não        →  engine + Care + MCP + loops   ← CẤM sửa
```

| Được | Cấm |
| --- | --- |
| App mới `ops/` (Vite + React + Tailwind + shadcn/ui) | Sửa `server/fanpage_care.py` policy/poller/classifier |
| Mount static `/ops` | Sửa engine, MCP Hub, `meta-pages-graph` |
| Module RBAC **mỏng** (mục 3) — ngoại lệ duy nhất phía server | Xoá/viết đè `dashboard/*.js` console chủ |
| Gọi API Care / Kanban / usage / inbox / sessions **đã có** | Endpoint Graph Facebook mới, tự gửi Zalo |

**Xung đột quyền:** User muốn “xiết role mặt trước” và “không đụng mặt sau”. Cookie admin hiện tại = 1 user `admin`, full máy. Ẩn menu bằng CSS **không phải quyền**. Gemini **được phép thêm** `server/ops_rbac.py` + vài dòng gắn vào auth hiện có. Không đụng bộ não.

Tham khảo UI (copy *cảm giác*, không clone pixel):

- [shadcn/ui Dashboard](https://ui.shadcn.com/examples/dashboard) — layout, card, bảng
- [Attio](https://attio.com) / Linear — CRM gọn, mật độ thông tin
- Tremor / Recharts — sparkline, bar theo ngày
- Font sẵn trong repo: `system/fonts/BeVietnamPro-*.woff2` (tiếng Việt). Accent cam `#f97316` + navy `#0f172a` (đồng bộ video Sao Việt). Mặc định **theme sáng** (nhân viên văn phòng); dark là toggle.

Stack:

```
ops/
  package.json          react 18, vite, typescript, tailwind, @tanstack/react-query, recharts
  src/pages/...
  src/components/ui/    shadcn
  src/lib/api.ts        fetch cookie-session tới origin Javis (same-origin)
  src/lib/rbac.ts
```

Build ra `ops/dist/`. FastAPI phục vụ `StaticFiles` tại `/ops` (HTML5 fallback `index.html`). Dev: Vite proxy `7777`.

---

## 1. Ba vai (role)

| Role | Ai | Thấy | Làm | Không bao giờ |
| --- | --- | --- | --- | --- |
| `staff` | CSKH / tư vấn | Tổng quan (rút), Hộp thư, Khách, Việc được giao | Gửi/từ chối **nháp**, Tạo việc từ comment, Javis nhận lại thread, ghi chú khách | Kill switch, settings Care, MCP, model, terminal, chat Javis, merge/xoá CRM, backup CRM |
| `manager` | Quản lý | Tất cả ops + Xu hướng + nhật ký Care | Mọi quyền staff + merge khách + đổi mode Care **suggest/auto** (không `full`) + xem chi phí token | Terminal, MCP raw, CLAUDE.md, `mode=full`, Kill (trừ khi owner) |
| `owner` | Chủ máy (admin hiện tại) | Ops **và** console `/` | Mọi thứ, gồm `full` + Kill + RBAC users | — |

Map mặc định: user `auth.username` hiện tại = `owner`. User ops khác lưu `STATE_DIR/ops_users.json` (hash mật khẩu **cùng hàm** `web_security` đang dùng cho admin — xem `server/main.py` `/auth/login`).

---

## 2. Màn hình (thứ tự ưu tiên)

### M0. Đăng nhập `/ops/login`

Form gọn, logo chữ “Sao Việt Ops” / “Javis Care”. Không lộ “Javis OS terminal”. Login gọi `/auth/login` hiện có **nếu** user là owner; user ops gọi `POST /ops/auth/login` (module RBAC). Session cookie riêng `ops_session` **hoặc** tái sử dụng cookie Javis nếu owner.

Sau login: `/ops` (Tổng quan).

### M1. Tổng quan — “Javis đã làm gì hôm nay”

Hero 6 thẻ (số từ `GET /fanpage-care/state` → `stats` + `eligible_pages`):

| Thẻ | Field |
| --- | --- |
| Bình luận 24h | `stats.events_24h` |
| Lead 24h | `stats.leads_24h` |
| Nháp chờ bạn | `stats.pending_drafts` (cảnh báo cam nếu >0) |
| Javis đã trả lời | `stats.replies_24h` |
| Cần người | `stats.human_needed_24h` |
| Khách trong CRM | `stats.total_customers` |

Dưới thẻ:

- **Dòng thời gian 20 sự kiện mới** (`GET /fanpage-care/inbox?limit=20`): icon class, page, 1 dòng nội dung, chip (FAQ đã gửi / nháp / lead).
- **Việc Kanban do Care tạo** (`GET /kanban` lọc `created_by=fanpage_care` nếu field có; không có thì hiện 5 task mới nhất).
- Cột phải: trạng thái Care (bật/tắt, mode, giờ im lặng, perm Facebook) — **staff chỉ xem**, manager được link “Mở Care” (vẫn trong /ops, không nhảy console).

Empty state: checklist 3 bước (Facebook Toàn quyền / bật Care / Quét) — copy từ `docs/dev/2026-09-16-fanpage-care-ui-plan.md`.

### M2. Hộp thư — thao tác chính của nhân viên

Hai tab: **Bình luận** | **Messenger**.

**Bình luận**

- Cột trái: lọc page (từ `eligible_pages`), chip class: Tất cả / Lead / FAQ / Spam / Cần người.
- Giữa: **card** comment (không bảng 6 cột). Mỗi card: page, giờ, class, tên, nội dung, SĐT che `090****567`, trạng thái (đã trả lời / nháp / bỏ qua).
- Phải (desktop) / drawer (mobile): nháp Javis nếu có. Staff: **Gửi** / **Sửa rồi gửi** / **Bỏ qua** / **Tạo việc**.
  - Gửi = `POST /fanpage-care/drafts/{id}/send`
  - Bỏ qua = `.../reject`
  - Tạo việc = `POST /fanpage-care/handoff`
  - “Sửa rồi gửi”: PATCH không có → **không bịa API**. v1: textarea local, vẫn gọi send với nội dung draft hiện có **chỉ khi** backend đã hỗ trợ message override. Nếu send không nhận body: ẩn nút Sửa, chỉ Gửi/Bỏ.

**Messenger**

- `GET /fanpage-care/conversations`
- Thread: page, PSID rút, cửa sổ 24h, chip takeover.
- `POST /fanpage-care/conversations/release-takeover` = “Javis nhận lại”.
- Banner Development 1 dòng.

### M3. Khách hàng (CRM)

- `GET /fanpage-care/customers?q=`
- Bảng: tên, SĐT (staff luôn che; manager có mắt hiện full), cơ sở, khoá, thẻ, lần cuối.
- Click = `GET /fanpage-care/customers/{id}` — panel markdown (timeline).
- Manager: Gộp (`POST .../merge`), Xoá (`DELETE .../{id}`).
- Staff: chỉ đọc + “Tạo việc gọi lại” (handoff).

### M4. Việc

- `GET /kanban` — danh sách, không giả Trello kéo thả phức tạp.
- 3 cột: Chờ / Đang làm / Xong (map status API thật — đọc `server/tasks.py` trước khi vẽ; **đừng bịa cột**).
- Click task: goal, `created_by`, execution_mode. Staff không `POST /kanban/run` (đó là cho Javis). Staff chỉ đọc + comment nếu API có; không thì chỉ đọc.

### M5. Xu hướng (manager + owner)

Không có API “analytics” riêng. **Tự tổng hợp ở frontend** từ inbox + stats + usage (React Query, không thêm backend):

- Cột: số comment 24h vs lead 24h vs replies (3 số stats).
- Pie/bar: phân bố `class` trên `GET /fanpage-care/inbox?limit=200` (đếm client).
- Bar: lead theo `campus` / page_id từ customers.
- Sparkline token 7 ngày: `GET /usage/summary` hoặc `/usage/tong-quan` — **chỉ manager/owner**. Staff không thấy tiền.

Nhãn: “Javis đọc được gì” / “Lead theo cơ sở” / “Tỷ lệ nháp vs đã gửi”. Không ghi “AI insight” bịa.

### M6. Nhật ký Javis (manager)

- `GET /inbox` (hòm thư hệ thống: digest 20h Care).
- `GET /connect/audit` nếu có.
- Không đọc file `.jsonl` từ browser. Không làm viewer log server.

### M7. Cài đặt Ops (owner)

- Danh sách user ops: tạo staff/manager, khoá, đổi role.
- Không hiện API key, OpenRouter, Claude login.

### Điều hướng

Sidebar hẹp: Tổng quan, Hộp thư, Khách, Việc, Xu hướng (ẩn staff), Nhật ký (ẩn staff), Users (owner). Footer: “Não: Javis · ẩn” + link owner-only “Buồng lái” → `/` (console). Staff **không thấy** link đó.

Topbar: tên user, role chip, page filter global, chuông = `pending_drafts` + inbox unread.

---

## 3. RBAC mỏng (ngoại lệ server)

File mới `server/ops_rbac.py` + `STATE_DIR/ops_users.json`:

```json
[{ "id": "u1", "username": "cskh1", "password_hash": "...", "salt": "...",
   "role": "staff", "enabled": true, "name": "Lan" }]
```

Endpoint:

| Method | Path | Ai |
| --- | --- | --- |
| POST | `/ops/auth/login` | public |
| POST | `/ops/auth/logout` | session |
| GET | `/ops/me` | session → `{username, role, name}` |
| GET/POST | `/ops/users` | owner |

Bọc **không sửa logic** các route Care/Kanban: helper `ops_require(*roles)` đọc session. Gắn vào:

| Path | staff | manager | owner |
| --- | --- | --- | --- |
| GET `/fanpage-care/state`, inbox, customers, conversations | ✓ | ✓ | ✓ |
| POST drafts send/reject, handoff, release-takeover | ✓ | ✓ | ✓ |
| POST customers/merge, DELETE customer | | ✓ | ✓ |
| POST `/fanpage-care/settings` | | mode≠full | ✓ |
| POST `/fanpage-care/poll-now` | | ✓ | ✓ |
| GET `/usage/*` | | ✓ | ✓ |
| GET `/kanban` | ✓ | ✓ | ✓ |
| POST `/kanban/run`, orchestration, `/settings`, `/mcp/*`, `/chat` | | | ✓ (console) |

Staff gọi URL cấm → **403**, không 200 + UI ẩn. Fail-closed.

Cookie ops không mở được `/` console nếu role ≠ owner (middleware: `/ops*` ok; còn lại yêu cầu owner). **Đây là chỗ xiết.** Nếu Gemini bỏ middleware, staff cầm cookie vào terminal — hỏng spec.

Owner vẫn login `/` như cũ, không bắt buộc qua `/ops`.

---

## 4. Map API có sẵn (đừng invent)

| UI | API |
| --- | --- |
| Thẻ tổng quan | `GET /fanpage-care/state` |
| Inbox comment | `GET /fanpage-care/inbox` |
| Gửi/bỏ nháp | `POST /fanpage-care/drafts/{id}/send` `.../reject` |
| CRM list/chi tiết | `GET /fanpage-care/customers` `GET .../customers/{id}` |
| Gộp/xoá | `POST .../merge` `DELETE .../{id}` |
| Messenger | `GET /fanpage-care/conversations` `POST .../release-takeover` |
| Handoff | `POST /fanpage-care/handoff` |
| Quét | `POST /fanpage-care/poll-now` |
| Care settings | `POST /fanpage-care/settings` |
| Kanban | `GET /kanban` `GET /kanban/health` |
| Hòm thư hệ thống | `GET /inbox` `POST /inbox/read` |
| Token/chi phí | `GET /usage/summary` `GET /usage/tong-quan` |
| Health | `GET /health` |

Trước khi vẽ, Gemini **đọc response JSON thật** (hoặc test) — field name theo server, không theo bảng này nếu lệch.

---

## 5. UX production (không thương lượng)

- Layout: sidebar 240px + main; mobile: bottom nav 5 mục (Tổng quan, Thư, Khách, Việc, Tôi).
- Empty / loading / error **đủ 3 trạng thái** mỗi trang (skeleton shadcn, không spinner giữa trang trắng).
- SĐT: `redact` mặc định; manager bấm mắt.
- Mọi write: toast thành công/thất bại; Gửi comment = confirm 1 lần (“Sẽ hiện công khai trên Facebook”).
- Tiếng Việt 100%. Không `perm`, `suggest`, `Graph` trên nhãn. Mode: Chỉ nháp / Tự FAQ / Tự động + tin.
- Không nhét chat Javis vào ops.
- Lighthouse-ish: font woff2 local, không Google Fonts CDN nếu VPS offline.
- Bảng khách: virtualize nếu >100 (TanStack Table).
- Poll 15s trên Hộp thư khi tab active; `document.hidden` thì dừng.

---

## 6. PR (Gemini làm đúng thứ tự)

**PR A — Skeleton SPA + mount**

- Scaffold `ops/` Vite React TS Tailwind shadcn.
- FastAPI: `app.mount("/ops", StaticFiles(..., html=True))` — **chỉ mount**, không sửa Care.
- Trang trống “Sao Việt Ops” + login mock.
- `ops/README.md` script `npm run build`.
- Bump không liên quan console cache.

**PR B — RBAC**

- `ops_rbac.py`, users json, login/me/users.
- Middleware 403. Test pytest: staff 403 `/mcp/list`, 200 `/fanpage-care/state`; owner 200 cả hai.
- Seed: owner = admin hiện tại. Lệnh/docs: owner tạo user staff trong M7.

**PR C — Tổng quan + Hộp thư + Khách** (MVP dùng được)

- React Query, pages M1–M3, card comment, draft actions, CRM panel.
- Role ẩn nút.

**PR D — Việc + Xu hướng + Nhật ký**

- M4–M6, Recharts từ inbox/stats/usage.

**PR E — Polish**

- Empty/skeleton, mobile bottom nav, redact SĐT, confirm gửi, BeVietnamPro, accent cam.
- `docs/29-ops-dashboard.md` hướng dẫn nhân viên (tiếng Việt, không jargon).

Definition of done MVP = **PR A+B+C**: nhân viên đăng nhập `/ops`, thấy số Javis 24h, gửi nháp, xem khách. Không cần vào `http://IP:7777/` console.

---

## 7. Việc Gemini **không** làm

- Không rewrite `dashboard/fanpage-care.js` trong PR này (UI Care console đã có plan riêng).
- Không Next.js / Remix (SSR không cần, VPS 4 GB).
- Không Firebase, không backend Nest riêng.
- Không tự bật Care `full`.
- Không commit `node_modules`. Build trên máy dev; VPS chỉ nhận `ops/dist` **hoặc** document `npm ci && npm run build` trong bước deploy hiện có — không bịa pipeline.

---

## 8. Kiểm thử

```
pytest tests/python/test_ops_rbac.py
cd ops && npm test   # vitest: redact, role-hidden buttons
```

Thủ công:

1. Owner: `/` console vẫn như cũ.
2. Tạo staff → login `/ops` → không vào được `/` (redirect hoặc 403).
3. Staff không thấy Xu hướng tiền token, không Kill, không merge.
4. Gửi nháp thật trên page test (mode suggest + bấm Gửi).
5. Mobile 390px: bottom nav, card không tràn.

---

## 9. Copy sidebar (đúng chữ)

- Tổng quan
- Hộp thư
- Khách hàng
- Việc
- Xu hướng
- Nhật ký
- Nhân sự (owner)

Phụ đề app: `Chăm sóc Fanpage · Javis chạy phía sau`

---

## 10. Câu trả lời sẵn cho “sao không sửa dashboard cũ?”

Console hiện tại = 19 trang Alpine, rail chủ máy, không multi-user. Nhét nhân viên vào đó là đưa terminal + MCP cho CSKH. App `/ops` tách mặt trước / mặt sau đúng yêu cầu; API không viết lại.
