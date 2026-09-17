# Phân tích + PROMPT GEMINI — Hỏi đáp Javis trên `/ops` (không clone `/app`)

Ý tưởng user: ngoài `/ops` cần **bot chat với Javis**, thân thiện kiểu Q&A, giống `/app` nhưng dễ dùng hơn.

**Kết luận:** Làm **được và nên làm** — với điều kiện **không** đưa CSKH vào não đầy đủ. Đó là trợ lý ca làm việc, không phải terminal.

---

## Phân tích (đọc trước khi code)

| | Chat `/app` | Chat `/ops` (đề xuất) |
|---|---|---|
| Ai | Chủ máy | CSKH / quản lý |
| Não | CLAUDE.md + mọi tool + shell (CLI) | **Không** shell, **không** MCP thô, **không** sửa settings |
| Giọng | Kỹ thuật Javis | Hỏi đáp ca: “nháp nào chờ?”, “khách này là ai?” |
| Gửi Facebook | Agent có thể gọi Graph | **Cấm** gửi Graph từ chat; bảo bấm Gửi trên hộp thư |
| Tài liệu | Cả vault | Kit **đúng phạm vi** + hướng dẫn `/ops` + số Care |

Lợi ích thi: nhân sự phổ thông hỏi tiếng Việt, không học 19 trang console.  
Rủi ro nếu clone `/app`: staff = full Javis → trái thuyết minh “403 buồng lái”.

**Không** dùng `chatbot_runtime` Telegram (bot khách / owner). Module mới: `ops_qa.py`.

---

## BẮT ĐẦU PROMPT GEMINI

Xây **Hỏi Javis** trên `/ops`: ô chat góc phải hoặc tab `Hỏi đáp`.

### 0. Cấm

- Spawn Claude Code / Codex / terminal.
- Tool `fb_page_reply`, `fb_message_send`, `fb_page_delete`, MCP, `/settings`, `/tiktok/post`.
- Đọc `CLAUDE.md` owner, `page_tokens.json`, PostPeer key.
- Trả lời ngoài phạm vi: bảo “mở Hộp thư / hỏi chủ máy”.

### 1. Hành vi

Model nhỏ: `aux_engine.complete_json` hoặc chat text **không tool nặng** (cùng lớp Care `complete_json`). Timeout 20s.

**Grounding trước lượt** (như `chatbot_grounding.py`, kho hẹp):

- `docs/28-cham-soc-fanpage.md`, `docs/29-ops-dashboard.md` (nếu có) — copy vận hành
- Brand kit **trong scope** (`pages_in_scope`) — giá/hotline chỉ từ đó
- Snapshot Care: `stats` 24h, số nháp comment/IB, kill switch, mode (JSON ngắn)

Không thấy file → nói không biết, **cấm bịa giá**.

**Tool chỉ đọc** (server gọi, không để model tự chọn Graph):

| Ý user | Server làm | Bot nói |
|---|---|---|
| Hôm nay thế nào | `get_stats` + scope | 3 comment chờ, 13 IB… |
| Khách X / SĐT | `search_customers` brand scope | Tên, tag, lần cuối — SĐT **che** với staff |
| Nháp nào | `list_drafts` kind+pending | “Mở Hộp thư tab …” + 3 dòng tóm tắt |
| Cách gửi / takeover | Đoạn docs | Không bấm gửi hộ |

POST `/ops/qa` body `{ message, scope }` → `{ reply, citations: [file], used_stats: true }`.  
Staff + manager + owner. Rate 20 câu / 10 phút / user.

### 2. UI `/ops`

- Nút nổi góc phải: **Hỏi Javis** (bubble). Panel 380px, mobile full.
- Placeholder: *“Nháp BSN hôm nay? Khách check ib là ai?”*
- Disclaimer 1 dòng: *Chỉ hỏi đáp ca làm. Gửi Facebook: nút trên Hộp thư.*
- Lịch sử session localStorage (xóa khi logout).
- Staff thấy SĐT đã che.

### 3. Prompt hệ thống (rút)

Bạn là trợ lý ca CSKH Javis Ops. Chỉ dùng tài liệu và số được nhét. Không gửi tin Facebook. Không hướng dẫn lấy token. Brand đang chọn: {scopeLabel}. Nếu hỏi giá mà kit không có số → bảo inbox/hotline kit, không bịa.

### 4. Test

- Staff POST `/ops/qa` 200; POST `/tiktok/post` vẫn 403.
- Hỏi “học phí” với kit không số → reply không chứa số tiền bịa.
- Hỏi “xóa page” → từ chối, bảo chủ máy.
- Mock aux_engine, không live LLM bắt buộc CI.

### 5. Done

`/ops` có bubble; câu “bao nhiêu nháp IB?” ra số thật theo scope; không có nút gửi Graph trong panel.

## HẾT

---

Ghi chú cho bạn: đây là **Q&A nội bộ**, không thay Care tự trả lời khách. Slide thi: *AI giúp nhân viên hỏi ca; khách vẫn do người (hoặc Care khi chủ bật).*
