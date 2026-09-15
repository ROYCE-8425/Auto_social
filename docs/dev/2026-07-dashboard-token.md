# Dashboard Token - Thiết kế (v1)

Ngày: 2026-07-18
Trạng thái: Spec, chờ duyệt
Người yêu cầu: Minh Quy

## 1. Mục tiêu

Một dashboard trong Javis để theo dõi mức tiêu thụ token, trả lời được 4 câu hỏi:

1. Tổng quan: kỳ này tiêu bao nhiêu token, so kỳ trước tăng hay giảm, có đang phình bất thường không.
2. Bóc tách: token đi vào đâu nhiều nhất - provider nào (Claude / Codex / OpenRouter-API), model nào, dự án nào, và của Javis thì là chat hay hoạt động ngầm (loop, lịch, subagent).
3. Hiệu quả: đang dùng tiết kiệm hay lãng phí (cache hit, token/phiên, output/input, chi phí quy đổi).
4. Hành động: sinh ra vài đề xuất cụ thể để tối ưu (giảm loop, hạ model, tách phiên, /compact...).

Người xem chính là Minh Quy (human-facing). Endpoint tổng hợp có thể tái dùng sau này cho một tool để chính Javis đọc, nhưng v1 không làm phần đó.

## 2. Nguồn dữ liệu và sự thật lịch sử

Có 3 nguồn, mức độ sẵn sàng khác nhau. Đây là điểm quan trọng nhất của thiết kế.

| Provider | Nguồn | Trường token | Lịch sử |
|---|---|---|---|
| Claude (Code + Javis-SDK) | `~/.claude/projects/**/*.jsonl` | input, output, cache_read, cache_creation (tách riêng) + model, cwd, entrypoint, isSidechain, sessionId, timestamp, gitBranch | Có đầy đủ, backfill được toàn bộ |
| Codex / ChatGPT | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | `total_token_usage` {input_tokens, cached_input_tokens, output_tokens, total_tokens} theo phiên | Có, backfill được |
| OpenRouter / OpenAI / Anthropic API (Javis chat thuần) | Hiện KHÔNG lưu. `engine.py` có trích `usage` mỗi lượt rồi ném đi; `conversations.db` không có cột token | Không có lịch sử | Chỉ có từ lúc bật ghi-log (forward-only) |

Hệ quả thiết kế: Claude và Codex có số ngay từ lịch sử. Nhánh API phải cắm một sink ghi-log nhẹ, và dashboard phải nói rõ "nhánh API chỉ có số từ ngày bật".

### Chi tiết trường Claude JSONL (đã xác minh trên máy)

Mỗi dòng `type=assistant` có:
- `timestamp` (UTC, hậu tố Z) - phải đổi sang giờ địa phương (Asia/Ho_Chi_Minh) khi chia theo ngày.
- `message.model`: `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-fable-5`, `claude-haiku-4-5-...`, `<synthetic>` (bỏ qua synthetic).
- `message.usage`: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `server_tool_use.web_search_requests/web_fetch_requests`.
- `entrypoint`: `sdk-cli`/`sdk-py`/`sdk-ts` (= Javis) vs `claude-desktop`/`claude-vscode` (= gõ tay).
- `cwd` (= dự án), `gitBranch`, `sessionId`, `isSidechain` (= token subagent).
- Tên thư mục project là slug hoá cwd; ưu tiên đọc `cwd` trong dòng để lấy dự án thật.

### Chi tiết Codex rollout

File JSONL theo phiên, có event mang `total_token_usage` (cộng dồn theo phiên) và `token_count`. Vì là cộng dồn, lấy giá trị lớn nhất hoặc dòng cuối của phiên làm tổng phiên; timestamp lấy từ tên file / event để xếp vào ngày.

## 3. Schema chuẩn hoá (usage event)

Mọi nguồn quy về một record chung trước khi gộp:

```
UsageEvent {
  ts            : epoch (đã đổi về local để bucket ngày)
  provider      : 'claude' | 'codex' | 'api'
  engine        : entrypoint gốc (sdk-cli, claude-desktop, codex, openrouter...)
  model         : chuỗi model chuẩn hoá
  project       : cwd hoặc '(codex)' / '(api)' nếu không có
  session_id    : id phiên (để đếm phiên, join, dedup)
  source        : 'javis' | 'manual'      # Claude: theo entrypoint; Codex/API = 'javis'
  activity      : 'chat' | 'background' | 'subagent' | 'manual'
  input         : token nạp mới (không gồm cache)
  output        : token sinh ra
  cache_read    : token đọc từ cache (rẻ)
  cache_create  : token tạo cache
  billable_in   : input + cache_read + cache_create  # tổng input tính tiền
}
```

## 4. Phân loại nguồn / hoạt động (attribution)

- `source`: Claude theo `entrypoint` (sdk-* = javis, desktop/vscode = manual). Codex và API luôn = javis.
- `activity` cho phần Javis:
  - `subagent`: dòng có `isSidechain = true` (token của agent con chạy ngầm trong bất kỳ phiên nào).
  - `chat`: `sessionId` của phiên Claude-SDK có mặt trong `conversations.db.cli_session_id` (tức phiên do người dùng mở qua dashboard/Telegram).
  - `background`: phiên Claude-SDK KHÔNG có trong `conversations.db` (loop, lịch hẹn, tự cải tiến, cron). Đây là "hoạt động ngầm".
  - `manual`: entrypoint gõ tay.
- Tinh chỉnh loop vs lịch (để sau v1): hiện gộp chung `background`. Muốn tách "loop X tốn bao nhiêu" cần Javis gắn nhãn khi spawn phiên (ví dụ ghi một map `sessionId -> {kind: loop, slug}` vào một sidecar). Ghi nhận là việc v1.1, không chặn v1.

Join key: `conversations.db.sessions.cli_session_id` = `sessionId` trong Claude JSONL. Đã xác minh 31/43 phiên có key này.

## 5. Bộ chỉ số

### 5.1 Thẻ KPI (đầu trang, đổi theo kỳ đang chọn + so kỳ trước)

- Tổng token trong kỳ (+ % delta so kỳ trước).
- Token/ngày trung bình (run-rate) và phóng chiếu hết kỳ (nếu kỳ chưa đóng).
- Cache hit rate = cache_read / billable_in. Chỉ số hiệu quả chính.
- Số phiên và token trung bình mỗi phiên (phát hiện phiên phình).
- Tỉ lệ output / input.
- Chi phí quy đổi ước tính (xem mục 7).

### 5.2 Bóc tách (biểu đồ)

- Theo provider: Claude / Codex / API (đây là bộ lọc chính; chọn provider thì cả trang lọc theo).
- Theo source: Javis vs gõ tay (chỉ áp dụng phần Claude).
- Theo activity của Javis: chat / background / subagent.
- Theo model: xếp hạng model ngốn token (kèm cột chi phí quy đổi).
- Theo dự án (cwd): top dự án.
- Theo thời gian: cột token mỗi ngày trong kỳ (stacked theo provider hoặc theo activity); thêm heatmap 24 giờ để thấy giờ nào chạy ngầm nhiều.

### 5.3 Insight tự động (danh sách đề xuất)

Sinh từ luật, mỗi luật ra 0..n dòng cảnh báo:

- Cache hit trung bình một dự án/phiên dưới ngưỡng (ví dụ < 50%) khi phiên dài -> gợi ý /compact hoặc chia phiên.
- Một nhóm `background` (loop/lịch) chiếm tỉ trọng token lớn (ví dụ > 25% kỳ) mà output nhỏ -> "hoạt động ngầm đang ngốn, xem lại tần suất".
- Model đắt (opus) chiếm phần lớn token cho phiên ngắn/việc vặt -> gợi ý hạ model.
- Phiên vượt ngưỡng token tuyệt đối (ví dụ > 1M billable_in) -> gợi ý tách.
- Token/ngày kỳ này vượt run-rate kỳ trước quá X% -> cảnh báo spike, chỉ ra nguồn tăng chính.

Ngưỡng để trong config, chỉnh được.

## 6. Kỳ thời gian và so sánh

Bộ lọc kỳ: hôm nay, hôm qua, tuần này, tuần trước, tháng này, tháng trước, 3 tháng gần nhất, năm nay. Cho phép chọn khoảng tuỳ ý (from/to) là bonus.

Mỗi kỳ tự so với kỳ tương đương liền trước (hôm nay vs hôm qua, tuần này vs tuần trước, tháng này vs tháng trước, 3 tháng vs 3 tháng trước đó, năm nay vs năm ngoái). Delta hiển thị ở thẻ KPI.

Timezone: Asia/Ho_Chi_Minh. JSONL Claude là UTC nên phải convert trước khi bucket ngày, nếu không ranh giới "hôm nay" sẽ lệch.

## 7. Chi phí quy đổi (pricing)

Một file `pricing.json` (đơn giá USD trên 1 triệu token) cho từng model: giá input, output, cache_read, cache_write. Cost ước tính = input*giá_in + output*giá_out + cache_read*giá_cacheread + cache_create*giá_cachewrite.

Ý nghĩa: với Claude/ChatGPT là gói subscription nên đây KHÔNG phải tiền thật, mà là "nếu tính theo API thì tốn ngần này" - cho thấy gói cước đang tiết kiệm bao nhiêu. Với OpenRouter/API là tiền thật. Dashboard ghi rõ nhãn "ước tính quy đổi" để không hiểu nhầm.

Bảng giá cần cập nhật tay khi có model mới; để trong config, không hard-code rải rác.

## 8. Kiến trúc kỹ thuật

Khớp stack hiện có: FastAPI (`server/main.py`) + JS thuần (`dashboard/`), không build tool.

### 8.1 `server/usage_index.py` (indexer)

- Quét 3 nguồn. Với mỗi file, ghi nhớ `(path, size, mtime)` đã xử lý; chỉ đọc file mới hoặc đã đổi (parse tăng dần). 594MB/1581 file nên bắt buộc incremental.
- Parse -> chuẩn hoá về `UsageEvent` -> ghi vào SQLite `server/usage_index.db` (gitignore, là dữ liệu dẫn xuất).
- Hai bảng: `files_seen(path, size, mtime, provider)` để biết đã index tới đâu; `usage_events(...)` hoặc bảng gộp sẵn `usage_daily(day, provider, source, activity, model, project, input, output, cache_read, cache_create, sessions)` để query nhanh. Có thể giữ cả event thô cho drill-down phiên, cân nhắc dung lượng.
- Hàm query: `summary(period, compare, provider=None)` trả KPI + breakdowns + timeseries; `insights(period)` chạy luật mục 5.3.
- Đọc `conversations.db` (read-only) để lấy tập `cli_session_id` phục vụ phân loại chat vs background.

### 8.2 Ghi-log nhánh API (forward)

- `engine.py` đã có 3 chỗ `yield {"type":"usage", ...}` (khoảng dòng 316, 492, 588). Thêm một hàm `usage_log.record(provider='api', engine, model, session_id, input, output, ...)` gọi tại các điểm đó, append vào `server/logs/usage-api.jsonl` (append-only, crash-safe). Indexer đọc file này như nguồn thứ 3.
- Thay đổi engine tối thiểu: một dòng gọi hàm ở mỗi điểm yield. Không đổi luồng chính.

### 8.3 Endpoints (FastAPI)

- `GET /usage/summary?period=&compare=&provider=&project=` -> JSON KPI + breakdowns + timeseries.
- `GET /usage/insights?period=` -> danh sách đề xuất.
- `POST /usage/refresh` -> chạy index tăng dần, trả số file mới xử lý.
- (tuỳ chọn) `GET /usage/session/{id}` -> chi tiết một phiên để drill-down.
- Bảo vệ bằng cùng cơ chế auth như các route dashboard khác.

### 8.4 Tab dashboard (UI)

- Thêm một tab "Token" vào `dashboard/index.html` + file `dashboard/usage.js` + style trong `style.css`.
- Thành phần: hàng chip lọc kỳ; dropdown/segmented lọc provider; hàng thẻ KPI; các biểu đồ breakdown; biểu đồ timeseries + heatmap; khối insight.
- Biểu đồ: dùng thư viện nhẹ nhúng sẵn (cân nhắc Chart.js một file, hoặc vẽ SVG tay để khỏi thêm dependency). Chốt ở bước lập kế hoạch.
- Nút "Làm mới" gọi `/usage/refresh` rồi reload số.

## 9. Phạm vi v1 và để sau

v1 (làm ngay):
- Indexer cho Claude + Codex (có lịch sử đầy đủ).
- Cắm ghi-log forward cho nhánh API (số tích dần từ khi bật).
- Đủ bộ KPI, breakdown (provider/source/activity/model/project/time), insight cơ bản, pricing quy đổi.
- Tab dashboard với đủ bộ lọc kỳ + lọc provider.

Để sau (v1.1+):
- Tách `background` thành loop vs lịch vs tự-cải-tiến (cần Javis gắn nhãn sessionId khi spawn).
- Drill-down tới từng phiên.
- Tool cho chính Javis đọc báo cáo token qua chat.
- Cảnh báo chủ động (đẩy Telegram khi spike).

## 10. Edge cases / rủi ro

- Timezone UTC->local: sai là lệch ranh giới ngày. Phải test.
- Codex `total_token_usage` là cộng dồn: đừng cộng mọi dòng, chỉ lấy tổng phiên.
- Model `<synthetic>` và dòng thiếu usage: bỏ qua, không tính.
- File đang được ghi (phiên đang chạy): đọc phần đọc được, lần refresh sau bù. Không khoá file.
- Dung lượng index: nếu giữ event thô, `usage_index.db` có thể lớn. Cân nhắc chỉ giữ `usage_daily` + tổng theo phiên, drop event thô cũ.
- Dedup: cùng một requestId/uuid không được đếm hai lần khi re-parse. Dùng khoá tự nhiên (uuid dòng) hoặc chỉ parse file chưa đổi.
- Fork sạch: `usage_index.db`, `usage-api.jsonl` là dữ liệu máy, phải vào `.gitignore`, không lên git.

## 11. Kiểm thử

- Unit: parser Claude (một dòng mẫu -> UsageEvent đúng), parser Codex (lấy tổng phiên đúng), phân loại activity (chat vs background theo có/không trong conversations.db), gom kỳ + so sánh, đổi timezone ranh giới ngày.
- Integration: chạy indexer trên một thư mục fixture nhỏ, gọi `/usage/summary` kiểm tra tổng khớp tay.
- Chạy test qua `.venv` của dự án (theo ghi chú: python hệ thống thiếu lib).

## 12. Danh sách việc (đưa sang bước lập kế hoạch)

1. `usage_index.py`: khung SQLite + files_seen + incremental scan.
2. Parser Claude JSONL -> UsageEvent (gồm entrypoint, isSidechain, cwd, cache).
3. Parser Codex rollout -> UsageEvent (tổng phiên).
4. Phân loại activity qua join `conversations.db`.
5. `pricing.json` + hàm tính chi phí quy đổi.
6. Hàm `summary()` + `insights()` + gom kỳ/so sánh + timezone.
7. `usage_log.record()` + cắm 3 điểm trong `engine.py` + parser đọc `usage-api.jsonl`.
8. Endpoints `/usage/summary`, `/usage/insights`, `/usage/refresh`.
9. Tab "Token" trong dashboard + `usage.js` + style + chọn thư viện biểu đồ.
10. Test unit + integration; cập nhật `.gitignore`.
```
