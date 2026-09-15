# 01 - Kiến trúc tổng quan

## Ý tưởng cốt lõi (đọc cái này trước hết)

Javis **không gọi thẳng API model**. Javis mượn **CLI dạng agent** của nhà cung cấp (Claude Code, Codex) làm bộ não, để tận dụng chính **gói subscription** người dùng đang trả thay vì bắt họ mua API riêng. Bộ não đó vốn đã biết đọc/ghi file, gọi MCP, chạy lệnh, dùng skill. Javis bọc quanh nó một dashboard, một Second Brain, và một lớp kiểm soát quyền.

Hệ quả kiến trúc quan trọng: **Javis là lớp điều phối, không phải lớp inference.** Khi debug "sao Javis trả lời sai", hãy hỏi trước: prompt bơm vào là gì, tool nào được phép, cwd trỏ vào brain nào. Đừng sửa model.

Vẫn có đường API thuần (OpenRouter/OpenAI/Anthropic/Gemini) cho ai không có subscription CLI, nhưng đường đó **chat thuần, không có MCP native của CLI** - bù lại bằng hub in-process (xem [trang 04](04-engine-hub-plugin-skill.md)).

## Bốn lớp

```
┌─────────────────────────────────────────────────────────┐
│ 1. DASHBOARD  (dashboard/*.js, thuần JS + Alpine)       │
│  Đồ thị tri thức + rail điều hướng + giọng nói (Web Speech) │
└───────────────┬─────────────────────────────────────────┘
                │ WebSocket /ws  (chat streaming)
                │ REST  /settings /skills /files /kanban ...
┌───────────────▼─────────────────────────────────────────┐
│ 2. SERVER  (server/main.py - FastAPI, ~120 endpoint)    │
│    + feature module: learn, tasks, reminders,           │
│      self_improve  (mỗi cái tự mang APIRouter riêng)    │
└───────────────┬─────────────────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
┌───────▼──────┐  ┌──────▼──────────────────────────────┐
│ 3. ENGINE    │  │ 4. MCP HUB  (mcp_hub.py)            │
│  bộ não      │◄─┤  cổng tool DUY NHẤT cho mọi engine  │
│  claude_sdk  │  │  - Claude/Codex thấy hub như 1 MCP  │
│  codex CLI   │  │    server http tên "javis"          │
│  engine.py   │  │  - engine API gọi in-process        │
│  (API thuần) │  │  Hub enforce 3 mức quyền + audit    │
└──────────────┘  └──────┬──────────────────────────────┘
                         │
              ┌──────────┴───────────┬──────────────┐
              ▼                      ▼              ▼
        MCP ngoài (POS,        Plugin Python    Skill router
        Ads, Calendar...)      (system/plugins) (SKILL.md)
```

Và nằm ngang qua tất cả: **BRAIN (vault)** - một thư mục `.md` là toàn bộ trí nhớ + năng lực của Javis. Xem [trang 05](05-brain-vault.md).

## Một lượt chat đi qua đâu

Đây là đường đi cần thuộc để debug bất cứ thứ gì:

1. **Trình duyệt** - user nói hoặc gõ. `dashboard/voice.js` (Web Speech API) hoặc `#chatInput`. `dashboard/app.js` mở WebSocket `/ws` và đẩy tin lên.
2. **`main.py` `/ws`** (khoảng dòng 4155) - nhận tin, dựng **system prompt**: nội dung `CLAUDE.md` + `MEMORY.md` của brain + chỉ mục skill + ngữ cảnh kênh (`channel_context.py`) + số liệu dùng.
3. **Chọn bộ não** - `_effective_main(cfg)` (`main.py:488`) đọc `settings.json → model.main = {provider, model}` và trả về provider đang là MAIN.
   - `anthropic-cli` → `claude_sdk_engine.py` (qua factory `claude_cli.claude_engine`)
   - `openai-oauth` → `CodexCLI` trong `claude_cli.py`
   - `openrouter` / `openai` / `anthropic-api` / `gemini` → `engine.py` (chat thuần, stream token)
4. **Engine chạy** và stream ra các event `{type: text | tool_call | tool_result | final | error}`. Đây là **hợp đồng chung** mà mọi engine phải tuân, xem docstring `claude_sdk_engine.py:1`.
5. **Tool call** (nếu có) đi qua **MCP Hub**: hub gộp tool của mọi connection, kiểm quyền, chạy, ghi audit.
6. **Stream về trình duyệt** qua WebSocket. `chat-render.js` render markdown, `voice.js` đọc thành tiếng.
7. **Sau lượt** - `learn.py` rewire bộ nhớ (có debounce, chỉ đọc, hoàn tác được); `sessions.py` lưu hội thoại vào SQLite + FTS5.

## State nằm ở đâu (hay nhầm chỗ này)

Có **ba** kho state khác nhau, đừng lẫn:

| Kho | Đường dẫn | Chứa gì | Ai sở hữu |
|-----|-----------|---------|-----------|
| **STATE_DIR** | `server/` (mặc định), hoặc `$JAVIS_STATE_DIR` = `/data/state` trên Docker | `settings.json` (có secret, đã mã hoá), branding, token hub, plugin enable-state, `conversations.db` | Javis, gitignored |
| **BRAIN (vault)** | `brains/<tên>/` | Ghi chú, Wiki, Memory, skills, agents, workflows, loops | Người dùng, đẩy được lên GitHub |
| **Code tree** | `server/`, `dashboard/`, `system/` | Mã nguồn + plugin/loop/catalog bundled | Repo. **Trên Docker là read-only** |

Cái bẫy: trong container, code tree read-only. Mọi thứ Javis tự ghi **phải** đi qua `STATE_DIR`. Đó là lý do logo tuỳ chỉnh nằm ở `STATE_DIR/branding` chứ không phải `dashboard/`, và enable-state của plugin bundled nằm ở `STATE_DIR/plugins.json` chứ không sửa vào `plugin.yaml` của app.

## Vào code từ đâu

| Muốn hiểu | Mở file |
|-----------|---------|
| Toàn bộ API + vòng đời app | `server/main.py` (đọc các dải banner `# =====`, xem [trang 02](02-backend.md)) |
| Cấu hình, đường dẫn, auth | `server/config.py` |
| Bộ não Claude | `server/claude_sdk_engine.py` |
| Bộ não API thuần | `server/engine.py` |
| Tool đi đâu, quyền chặn ở đâu | `server/mcp_hub.py` + `server/mcp_catalog.py` |
| Giao diện, rail, các trang | `dashboard/console.js` |
| Chat, WebSocket, giọng nói | `dashboard/app.js` + `dashboard/voice.js` |
