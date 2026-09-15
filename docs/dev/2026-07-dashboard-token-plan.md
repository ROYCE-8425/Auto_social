# Dashboard Token - Kế hoạch triển khai

> **Cho worker:** thực thi theo superpowers:executing-plans (inline) hoặc subagent-driven. Mỗi task có checkbox và kết thúc bằng một deliverable test được độc lập. TDD, commit theo task.

**Goal:** Nâng trang "Mức dùng" thành dashboard token thật: lọc theo kỳ (hôm nay ... năm nay), so kỳ trước, bóc tách provider/nguồn/hoạt động/model/dự án, cache hit, chi phí quy đổi, và insight hành động - đọc từ log thô Claude + Codex (có lịch sử) và usage_store (nhánh API, forward).

**Architecture:** Một indexer (`usage_index.py`) quét `~/.claude/projects/**/*.jsonl` + `~/.codex/sessions/**/rollout-*.jsonl`, parse tăng dần (bỏ file chưa đổi), phân loại hoạt động bằng join `conversations.db.cli_session_id`, gộp vào SQLite `STATE_DIR/usage_index.db`. Nhánh API (openrouter/openai/anthropic) không có log thô nên đọc từ append-only `STATE_DIR/usage-events.jsonl` mà `usage_store.record()` ghi thêm. Endpoint `/usage/summary|insights|refresh` phục vụ tab dashboard JS thuần (vẽ SVG tay, không thêm dependency).

**Tech Stack:** Python 3 + sqlite3 (chuẩn thư viện), FastAPI (đã có), JS thuần + SVG (đã có). Test: script python thuần chạy qua `.venv`, tự cô lập temp dir (KHÔNG pytest).

## Global Constraints

- Tuyệt đối KHÔNG ký tự em dash (U+2014) trong mọi file/code/comment. Dùng "-".
- Timezone tính ngày: Asia/Ho_Chi_Minh (UTC+7). JSONL Claude là UTC (hậu tố Z) nên phải convert trước khi bucket ngày.
- Không phá `usage_store.py` / `/usage` / trang "Mức dùng" hiện có (chúng vẫn chạy).
- Test theo mẫu dự án: script python thuần, `os.environ["JAVIS_STATE_DIR"]=tempdir`, chạy `cd server && ../.venv/Scripts/python.exe test_x.py`, exit code != 0 nếu fail.
- Nguồn dữ liệu phải override được qua env để test: `JAVIS_CLAUDE_PROJECTS_DIR`, `JAVIS_CODEX_SESSIONS_DIR` (mặc định `~/.claude/projects`, `~/.codex/sessions`).
- Provider raw-log = authoritative cho `claude` + `codex`. `usage-events.jsonl` = authoritative CHỈ cho provider API (openrouter/openai/anthropic-api/oauth). Không double-count.
- Không commit dữ liệu dẫn xuất: thêm `.gitignore` cho `usage_index.db*`, `usage-events.jsonl*`.
- STATE_DIR mặc định = thư mục `server/` (config.py: `JAVIS_STATE_DIR` fallback `__file__.parent`).

---

## File Structure

- Create `server/usage_parsers.py` - hàm parse thuần (Claude line, Codex file, api-event line) -> UsageEvent dict. Không I/O ngoài đọc file được truyền path.
- Create `server/usage_pricing.json` - bảng giá USD/1M token theo model.
- Create `server/usage_index.py` - schema SQLite, quét tăng dần, phân loại activity, `refresh()`, `summary()`, `insights()`, `estimate_cost()`.
- Modify `server/usage_store.py` - trong `record()` append thêm 1 dòng vào `STATE_DIR/usage-events.jsonl`.
- Modify `server/main.py` - thêm `GET /usage/summary`, `GET /usage/insights`, `POST /usage/refresh` (giữ `/usage` cũ).
- Create `dashboard/usage.js` - UI dashboard giàu (filter kỳ + provider, KPI cards, chart, insight).
- Modify `dashboard/console.js` - `renderUsage()` delegate sang `usage.js` (giữ phần số dư OpenRouter).
- Modify `.gitignore` - thêm index db + events log.
- Test: `server/test_usage_parsers.py`, `server/test_usage_index.py`.

## UsageEvent (khoá chung, dict)

```
{ ts:int(epoch), day:'YYYY-MM-DD'(local), provider:'claude'|'codex'|'api',
  engine:str, model:str, project:str, session_id:str,
  source:'javis'|'manual', activity:'chat'|'background'|'subagent'|'manual',
  input:int, output:int, cache_read:int, cache_create:int }
```
`billable_in = input + cache_read + cache_create`.

---

### Task 1: UsageEvent + parser Claude line

**Files:** Create `server/usage_parsers.py`; Test `server/test_usage_parsers.py`

**Produces:** `parse_claude_line(obj: dict, chat_sessions: set[str]) -> dict | None`
- obj = một dòng JSONL đã json.loads. Trả None nếu: type != 'assistant', model == '<synthetic>', không có message.usage, hoặc tổng token = 0.
- source: 'javis' nếu entrypoint bắt đầu 'sdk', else 'manual'.
- activity: 'subagent' nếu isSidechain; else nếu source manual -> 'manual'; else 'chat' nесли session_id in chat_sessions else 'background'.
- day: đổi timestamp UTC -> UTC+7 -> 'YYYY-MM-DD'.
- project: basename của cwd (giữ cả path đầy đủ ở field riêng nếu cần); provider 'claude'.

- [ ] Step 1: viết test `test_parse_claude_line` với 1 dòng mẫu thật (sdk-cli, có cache) -> assert provider claude, source javis, activity background (session không thuộc chat set), billable gồm cache, day đúng UTC+7 (dùng timestamp gần nửa đêm UTC để bắt lỗi tz).
- [ ] Step 2: chạy test, thấy FAIL (hàm chưa có).
- [ ] Step 3: viết `parse_claude_line`.
- [ ] Step 4: chạy test, PASS.
- [ ] Step 5: thêm test: dòng synthetic -> None; dòng manual (claude-desktop) -> activity 'manual', source 'manual'; dòng isSidechain -> 'subagent'; session_id in chat_sessions -> 'chat'. PASS.
- [ ] Step 6: commit.

### Task 2: Parser Codex rollout

**Files:** Modify `server/usage_parsers.py`; Test `server/test_usage_parsers.py`

**Produces:** `parse_codex_file(path: str) -> dict | None`
- Đọc file rollout JSONL. Lấy `total_token_usage` (cộng dồn) - dùng dòng CUỐI có total_token_usage làm tổng phiên (input_tokens, cached_input_tokens, output_tokens). Nếu không có -> None.
- ts: từ timestamp event đầu/cuối hoặc parse tên file `rollout-YYYY-MM-DDTHH-...`. model: từ event nếu có, else 'codex'. provider 'codex', source 'javis', activity 'background' (Codex chạy nền theo mặc định; nếu về sau map được sang chat thì chỉnh). session_id = tên file.
- Map: input = input_tokens - cached_input_tokens (token mới), cache_read = cached_input_tokens, output = output_tokens, cache_create = 0.

- [ ] Step 1: viết fixture nhỏ (2-3 dòng jsonl có total_token_usage tăng dần) + test assert lấy đúng tổng phiên (không cộng mọi dòng), day đúng.
- [ ] Step 2: chạy FAIL.
- [ ] Step 3: viết `parse_codex_file`.
- [ ] Step 4: chạy PASS.
- [ ] Step 5: commit.

### Task 3: Bảng giá + chi phí quy đổi

**Files:** Create `server/usage_pricing.json`; Modify `server/usage_parsers.py` (hàm `estimate_cost`); Test `server/test_usage_parsers.py`

**Produces:** `estimate_cost(ev: dict, prices: dict) -> float`
- prices: { model_prefix: {in, out, cache_read, cache_write} } USD/1M. Match theo prefix dài nhất; fallback {0,0,0,0}.
- cost = (input*in + output*out + cache_read*cache_read + cache_create*cache_write)/1e6.
- pricing.json seed: opus-4-8, opus-4-7, sonnet, haiku, fable, gpt-4o..., với giá gần đúng (ghi rõ cập nhật tay). Model API openrouter đa dạng nên fallback 0 chấp nhận được.

- [ ] Step 1: test `estimate_cost` với 1 event opus + bảng giá mẫu -> assert số đúng theo công thức.
- [ ] Step 2: FAIL.
- [ ] Step 3: tạo pricing.json + hàm.
- [ ] Step 4: PASS.
- [ ] Step 5: commit.

### Task 4: Indexer SQLite + quét tăng dần (Claude + Codex)

**Files:** Create `server/usage_index.py`; Test `server/test_usage_index.py`

**Consumes:** parse_claude_line, parse_codex_file (Task 1-2).
**Produces:**
- `db_path() -> Path` = STATE_DIR/usage_index.db.
- `_chat_sessions() -> set[str]` đọc read-only `conversations.db` (cli_session_id không rỗng). Lỗi/thiếu file -> set() (không chặn).
- `refresh() -> dict{claude_files, codex_files, events}`: quét 2 nguồn (path từ env override), bỏ file có (path,size,mtime) đã thấy trong bảng `files_seen`, parse, cộng vào bảng `usage_daily(day, provider, source, activity, model, project, input, output, cache_read, cache_create, sessions)` (UPSERT cộng dồn; đếm session distinct qua bảng phụ hoặc set trong RAM khi build). Ghi files_seen. Idempotent.
- Schema `files_seen(path PK, size, mtime, provider)`; `usage_daily` khoá tổng hợp (day,provider,source,activity,model,project).

- [ ] Step 1: test dựng temp: tạo `JAVIS_CLAUDE_PROJECTS_DIR` với 1 file jsonl 2 dòng assistant (1 background, 1 subagent) + `JAVIS_CODEX_SESSIONS_DIR` 1 rollout. Chạy `refresh()`; assert tổng token khớp tay + phân loại đúng. Chạy `refresh()` lần 2; assert KHÔNG tăng (idempotent, files_seen chặn).
- [ ] Step 2: FAIL.
- [ ] Step 3: viết usage_index (schema + refresh + classify).
- [ ] Step 4: PASS (cả idempotent).
- [ ] Step 5: test file đổi (append dòng + đổi mtime/size) -> refresh lần 3 chỉ cộng phần mới. PASS.
- [ ] Step 6: commit.

### Task 5: usage_store ghi event forward + indexer nạp nhánh API

**Files:** Modify `server/usage_store.py`; Modify `server/usage_index.py`; Test `server/test_usage_index.py`

**Produces:**
- `usage_store.record(...)`: thêm append 1 dòng JSON `{ts, provider, model, in, out, cost}` vào `STATE_DIR/usage-events.jsonl` (append-only, best-effort try/except, không phá luồng chat). usage.json giữ nguyên hành vi (30 ngày) cho panel cũ.
- `usage_index`: trong refresh, đọc `usage-events.jsonl`, CHỈ lấy dòng provider in {openrouter, openai, anthropic, anthropic-api, oauth} (map về provider 'api'), cộng vào usage_daily (source javis, activity chat, project '(api)'). Theo dõi offset đã đọc trong files_seen (dùng size làm offset) để không đọc lại.

- [ ] Step 1: test: gọi `usage_store.record('openrouter','x/y',100,50)`; assert `usage-events.jsonl` có 1 dòng đúng. Rồi `usage_index.refresh()`; assert provider 'api' xuất hiện với 150 token. record thêm 1 dòng -> refresh -> chỉ cộng phần mới.
- [ ] Step 2: FAIL.
- [ ] Step 3: sửa usage_store + usage_index.
- [ ] Step 4: PASS.
- [ ] Step 5: commit.

### Task 6: summary() - kỳ + so sánh + breakdowns

**Files:** Modify `server/usage_index.py`; Test `server/test_usage_index.py`

**Produces:** `summary(period: str, provider: str|None=None, project: str|None=None) -> dict`
- period in {today, yesterday, this_week, last_week, this_month, last_month, last_3_months, this_year}. Giải ra (start_day, end_day) local + kỳ trước tương đương.
- Trả: `kpi` {tokens, tokens_prev, delta_pct, per_day_avg, sessions, avg_per_session, cache_hit, out_in_ratio, cost_est}; `by_provider`, `by_source`, `by_activity`, `by_model`(top+cost), `by_project`(top); `timeseries` [{day, providers...}]. Lọc theo provider/project nếu truyền.
- cache_hit = sum(cache_read)/sum(billable_in).

- [ ] Step 1: test: seed usage_daily bằng insert tay các ngày biết trước (hôm nay + hôm qua + tháng trước). Gọi summary('today') assert tokens + delta vs 'yesterday' đúng; summary('this_month') gồm đúng các ngày; cache_hit đúng; by_provider cộng đúng.
- [ ] Step 2: FAIL.
- [ ] Step 3: viết period-resolver (UTC+7) + summary.
- [ ] Step 4: PASS.
- [ ] Step 5: test ranh giới tz: một event lúc 23:30 UTC phải thuộc ngày HÔM SAU local. PASS.
- [ ] Step 6: commit.

### Task 7: insights()

**Files:** Modify `server/usage_index.py`; Test `server/test_usage_index.py`

**Produces:** `insights(period: str) -> list[dict{level, title, detail}]` theo luật mục 5.3 spec (cache thấp, background ngốn nhiều, model đắt việc vặt, phiên phình, spike vs run-rate). Ngưỡng hằng số đầu file.

- [ ] Step 1: test: seed dữ liệu kích mỗi luật (vd background chiếm 40% + spike) -> assert có đúng các insight tương ứng; seed "sạch" -> list rỗng/ít.
- [ ] Step 2: FAIL.
- [ ] Step 3: viết insights.
- [ ] Step 4: PASS.
- [ ] Step 5: commit.

### Task 8: Endpoints FastAPI

**Files:** Modify `server/main.py` (gần `/usage` cũ, ~dòng 2753); dùng `import usage_index`.

**Produces:**
- `GET /usage/summary?period=&provider=&project=` -> `usage_index.summary(...)` (gọi refresh() nhẹ trước nếu muốn số mới; hoặc để client bấm refresh). Mặc định: refresh tăng dần rồi summary.
- `GET /usage/insights?period=` -> insights.
- `POST /usage/refresh` -> refresh(), trả thống kê.
- Theo đúng kiểu route hiện có (không thêm auth đặc biệt; `/usage` cũ không có).

- [ ] Step 1: thêm 3 route.
- [ ] Step 2: smoke bằng script: khởi động import app? Thay vào đó test gián tiếp qua gọi thẳng `usage_index.summary` đã phủ ở Task 6; endpoint chỉ là vỏ. Verify tay bằng curl khi chạy app ở Task 9.
- [ ] Step 3: commit.

### Task 9: Tab dashboard (UI)

**Files:** Create `dashboard/usage.js`; Modify `dashboard/console.js` (renderUsage delegate); Modify `.gitignore`.

**Produces:** UI: hàng chip kỳ (8 lựa chọn), segmented lọc provider (Tất cả/Claude/Codex/API), hàng KPI cards (tổng+delta, token/ngày, cache hit, phiên, avg/phiên, chi phí quy đổi), chart cột token theo ngày (SVG tay, stacked theo provider), bảng breakdown model/dự án, danh sách insight. Nút "Làm mới" -> POST /usage/refresh rồi tải lại. Giữ khối số dư OpenRouter cũ.

- [ ] Step 1: viết usage.js render từ `/usage/summary` + `/usage/insights`; console.js gọi sang.
- [ ] Step 2: thêm `.gitignore`: `server/usage_index.db*`, `server/usage-events.jsonl*`.
- [ ] Step 3: chạy app (skill run / preview), mở trang Mức dùng, đổi kỳ + provider, xác nhận số đổi + chart vẽ + insight hiện. Screenshot.
- [ ] Step 4: commit.

### Task 10: Verify tổng + dọn

- [ ] Step 1: chạy cả `test_usage_parsers.py` + `test_usage_index.py` qua `.venv`, tất cả PASS.
- [ ] Step 2: chạy `refresh()` thật trên dữ liệu máy, kiểm tra tổng token một tháng khớp cảm quan (so panel cũ).
- [ ] Step 3: xác nhận `git status` không thấy db/jsonl dẫn xuất.
- [ ] Step 4: bump VERSION + CHANGELOG, commit, push (theo thói quen auto-push sau khi test OK).

## Self-review (đã soát)

- Phủ spec: nguồn (T1,2,5), schema (T1), phân loại (T1,4), pricing (T3), KPI/breakdown (T6), insight (T7), endpoint (T8), UI+kỳ+provider (T9), test (mọi task). Forward API (T5). Timezone (T1,6). Không double-count (Global + T5). OK.
- Không placeholder: mỗi task có signature thật + test cụ thể. Chart lib đã chốt (SVG tay, không dependency).
- Nhất quán tên: parse_claude_line/parse_codex_file/estimate_cost/refresh/summary/insights dùng đồng nhất giữa các task.
