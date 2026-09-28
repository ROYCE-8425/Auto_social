# PROMPT GEMINI — Agent / Skill / Workflow: TikTok + trả lời comment

Dán từ **BẮT ĐẦU**. Ảnh `/app` Plugins chỉ là **tool**. Skill/Agent/Workflow là 3 rail khác. Care comment **không** viết thành agent poller thứ hai.

---

## BẮT ĐẦU

### 0. Phân tầng (đừng nhầm Plugins)

| Tầng | Đã có | Việc Gemini |
|---|---|---|
| **Plugin (tool)** | `fb_page_*`, `fb_message_send`, `postpeer_tiktok_post`, `postpeer_tiktok_photos` | Không viết plugin mới |
| **Skill** | `dang-bai-facebook`, `viet-bai-facebook`, **`dang-video-tiktok`** (chỉ video URL) | Bổ sung skill carousel + skill soạn nháp comment **khi chat** |
| **Loop** | `dang-bai-hang-ngay*`, **`dang-video-tiktok-hang-ngay`** (`enabled: false`) | Sửa loop TikTok gọi `postpeer_tiktok_photos` + `/tiktok-media` |
| **Agent** | chỉ `agents/bien-tap-facebook.md` | **1 agent** `bien-tap-tiktok.md` |
| **Workflow** | chỉ `workflows/dang-bai-that-facebook.md` | **1 workflow** `dang-tiktok-carousel.md` |
| **Care Python** | `fanpage_care.py` poll + classifier + `/ops` | **Cấm** agent “lặp đọc comment” — trùng poller, đốt token, double-reply |

### 1. Có nên xây không?

| Nhu cầu | Nên? | Hình |
|---|---|---|
| Đăng TikTok tự động như Facebook | **Có** | Skill + Agent + Workflow + Loop (cùng kiểu `bien-tap-facebook`) |
| Trả lời comment/IB 24/7 | **Không** skill/agent | Giữ Care + `/ops`. Agent chat chỉ khi chủ gõ “soạn nháp comment này” |
| Plugin mới trên ảnh | **Không** | Tool đã đủ |

Care = zero-token preflight. Nhét comment vào Agent/Claude mỗi 5 phút = VPS 4GB chết + spam Graph.

### 2. Làm: Đăng TikTok (na ná Facebook)

**Skill** `skills/dang-carousel-tiktok/SKILL.md` (mới, hoặc mở rộng `dang-video-tiktok`):

1. `pick_next_tiktok.py` → NEXT=NONE thì dừng.
2. Brand từ kit: BSN vs đào tạo — **cấm** caption chéo.
3. 4–6 ảnh 9:16: dataset `game-bsn/<slug>/` hoặc `_xuat-tiktok/` → URL `https://trannhuy.online/tiktok-media/...`.
4. Cover AI: `javis_generate_image` `portrait` (tùy chọn).
5. Caption 8–18 dòng (skill hiện có).
6. `postpeer_tiktok_photos(..., auto_add_music=true)`.
7. `--ok` / ghi `tiktok-posts.jsonl`.

**Agent** `agents/bien-tap-tiktok.md`: skills `[dang-carousel-tiktok]`. Brief = 1 kit. Cấm mock post_id. Cấm Facebook tool. Cấm key PostPeer trong markdown.

**Workflow** `workflows/dang-tiktok-carousel.md`: 1 step agent trên. `status: on` nhưng loop file **`enabled: false`** đến khi Đăng thử `/app` live xong.

**Loop** sửa `dang-video-tiktok-hang-ngay.md`: gọi photos + media URL, không chỉ `postpeer_tiktok_post` video CDN giả.

Copy UI `/app` Agents/Workflows: tên **Đăng TikTok carousel**, không “Sao Việt”.

### 3. Làm mỏng: Skill soạn nháp khi CHAT (không thay Care)

**Skill** `skills/soan-nhap-tuong-tac/SKILL.md`:

- Khi user/`/app` chat: “trả lời comment này: …” hoặc dán `comment_id`.
- Đọc kit đúng `page_id` (BSN ≠ đào tạo).
- Gọi **không** poll. Chỉ: `fb_page_comments` / thread nếu cần → soạn 1 câu → `fb_page_reply` **sau confirm** hoặc để user bấm `/ops`.
- IB: `fb_conversation_thread` + `fb_message_send` sau confirm.
- Cấm tự loop. Cấm spawn mỗi comment.

**Không** tạo agent `cham-soc-fanpage` chạy interval. Đó là Care.

### 4. Test / Done

- File agent + workflow + skill carousel tồn tại, frontmatter đúng (`type: agent` / `workflow`).
- Rail `/app` Agents & Workflows hiện 2 mục (FB + TikTok), **không** chữ trung tâm cũ trên nhãn contest.
- Loop TikTok `enabled: false`.
- Không file agent đọc comment định kỳ.
- Pytest không bắt buộc live PostPeer.

### 5. Cấm

- Agent poller Care.
- Workflow “trả lời mọi comment”.
- Plugin trùng `postpeer_*`.
- Caption đào tạo lên kit BSN.

## HẾT

Thứ tự: skill carousel → agent → workflow → sửa loop. Skill soạn nháp chat = P1. Care giữ nguyên.
