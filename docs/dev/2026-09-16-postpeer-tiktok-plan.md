# Plan: Javis đăng video TikTok qua PostPeer (không thay Facebook Graph)

| Trường | Giá trị |
| --- | --- |
| **Cho** | Gemini implement |
| **Ngày** | 2026-09-16 |
| **Mục tiêu v1** | Javis tự đăng **1 video TikTok / vòng**, giống loop Fanpage: kit + caption + đăng thật |
| **Bên thứ 3** | [PostPeer](https://www.postpeer.dev) — BYO API key, trả phí theo credit |
| **Không làm** | Đưa Fanpage qua PostPeer; sửa `meta-pages-graph`; sửa Care/ops RBAC |

Facebook giữ nguyên: `/connect/facebook/pages` + Graph + Care. PostPeer **chỉ TikTok** (và chỗ trống cho Reels/Shorts sau, không code v1).

---

## 0. Vì sao PostPeer, không TikTok chính chủ

TikTok Content Posting API = tạo app + audit lâu. PostPeer lo OAuth, 1 endpoint `POST https://api.postpeer.dev/v1/posts`. OSS: user tự dán key (cùng mô hình Apify `facebook-monitor`).

Giá (2026): 20 credit free; 1 video TikTok ≈ 1 credit. Key **không** commit git.

Ràng buộc kỹ thuật (đọc docs trước khi code):

- Auth: header `x-access-key: KEY` (hoặc `Authorization: Bearer`).
- Nối TK: `GET /v1/connect/tiktok` → URL OAuth; sau đó `GET /v1/connect/integrations` lấy `accountId`.
- **Bắt buộc trước khi đăng:** `get_tiktok_creator_info` → `privacyLevel` phải nằm trong `privacyLevelOptions` TikTok trả.
- Media: `mediaItems[].url` phải là **HTTPS công khai** (không file local). Video dọc 9:16, mp4.
- `draft: true` nếu app chưa audit Direct Post → video vào inbox TikTok, user bấm đăng. v1 chấp nhận draft; báo rõ `status` + link.
- Không dùng MCP hosted `mcp.postpeer.dev` làm đường chính (khóa tool tên họ). Làm **plugin bundled** như Apify.

---

## 1. PostPeer cho phép làm gì trên TikTok (chọn / hoãn)

| Khả năng API | v1 | Sau |
| --- | --- | --- |
| Đăng video + caption + hashtag | **Làm** | |
| Privacy / tắt comment-duet-stitch | **Làm** (mặc định public, comment bật) | |
| Lên lịch `scheduledFor` | Hoãn | Loop Javis đã có giờ |
| Ảnh / carousel TikTok | Hoãn | Video trước |
| Cross-post Reels + Shorts cùng 1 file | Hoãn | 1 request `platforms[]` |
| Analytics views/likes | Sau khi có ≥1 bài | `/ops` Xu hướng |
| Comments API | **Không** TikTok trên marketing PostPeer (Comments = IG/FB/Threads) | Đừng hứa inbox TikTok |
| Messaging TikTok | Sau, API có nhưng khác Care FB | |
| `tiktok-ads` MCP hiện có | **Không đụng** | Ads ≠ đăng video |

v1 = **đăng video tự động**. Không Care comment TikTok.

---

## 2. Gắn vào Javis (file)

### 2.1 Connector catalog

`system/mcp-catalog.json` — entry mới, copy xương `facebook-monitor` (apikey):

```json
{
  "id": "postpeer",
  "name": "TikTok (PostPeer)",
  "category": "Mạng xã hội",
  "status": "beta",
  "transport": "http",
  "url": "",
  "auth": {
    "type": "apikey",
    "fields": [
      { "key": "postpeer_key", "label": "PostPeer access key", "placeholder": "pp_...", "env": "POSTPEER_API_KEY" }
    ],
    "guide": "1. Đăng ký postpeer.dev (20 credit free).\n2. Dashboard → Access Keys → copy key.\n3. Dán vào đây, bấm Kết nối.\n4. Vào postpeer.dev/dashboard bấm Connect TikTok (OAuth).\n5. Gọi tool postpeer_accounts để lấy accountId, ghi vào brand kit.\n\nKHÔNG dùng PostPeer để đăng Facebook — Fanpage đi Graph Javis.\nMỗi video TikTok trừ 1 credit."
  },
  "tool_meta": {
    "read": ["postpeer_accounts", "postpeer_tiktok_creator", "postpeer_post_get"],
    "danger": ["postpeer_tiktok_post"]
  },
  "default_perm": "readonly",
  "risk": "Mức Toàn quyền cho phép Javis ĐĂNG VIDEO lên TikTok đã nối. Hành động thật, có thể công khai hoặc vào inbox TikTok (draft).\nGiữ Chỉ đọc thì chỉ liệt kê tài khoản.\nKey PostPeer = chìa mọi mạng đã nối trên tài khoản PostPeer — đừng đưa staff."
}
```

Icon: dùng logo TikTok nếu có trong `dashboard/static/logos/`; không thì text. **Không** lấy logo PostPeer làm icon kênh (user tưởng não là PostPeer).

### 2.2 Plugin bundled

`system/plugins/postpeer-tiktok/` (`plugin.yaml` + `plugin.py`) — khuôn `fb-monitor-apify`:

- `CONNECTOR_ID = "postpeer"`
- `_token()` từ `mcp_store.connection_secrets`
- `GRAPH` không dùng; `BASE = "https://api.postpeer.dev/v1"`
- Header `x-access-key`

**Tools**

| Tool | min_mode | Việc |
| --- | --- | --- |
| `postpeer_accounts` | readonly | GET integrations; trả `accountId`, platform, username. **Cấm** lộ access key. |
| `postpeer_tiktok_creator` | readonly | GET creator info cho `account_id`. Trả `privacyLevelOptions`. |
| `postpeer_tiktok_post` | **full** | POST `/posts`. Bắt buộc `account_id` + `video` (URL https hoặc path trong vault) + `caption`. |
| `postpeer_post_get` | readonly | GET `/posts/{id}` — poll status. |

`postpeer_tiktok_post` logic:

1. `_check()` chưa key → ERROR hướng dẫn Kết nối.
2. Connection perm không full / loop không full → Hub chặn (khai `danger`).
3. `video`:
   - `http(s)://...` dùng thẳng.
   - Path vault (`attachments/...mp4`): **upload lên chỗ HTTPS**. Thứ tự: (a) nếu Javis đang public `https://trannhuy.online` và file nằm vault → URL kiểu site tĩnh **chỉ khi** file đã nằm CDN user (vd `tinhocsaoviet.com/storage/videos/...`). **Cấm** bịa URL. (b) Nếu PostPeer có `POST /v1/media` (Gemini **probe docs** lúc implement; có thì upload bytes, lấy url). (c) Không upload được → ERROR rõ: “Cần URL https công khai, file local chưa public.”
4. Gọi creator_info; chọn `privacyLevel` = `PUBLIC_TO_EVERYONE` nếu có trong options, không thì option đầu + `draft: true`.
5. Body:

```json
{
  "content": "<caption>",
  "platforms": [{
    "platform": "tiktok",
    "accountId": "<id>",
    "platformSpecificData": {
      "privacyLevel": "...",
      "disableComment": false,
      "disableDuet": false,
      "disableStitch": false,
      "draft": <bool>
    }
  }],
  "mediaItems": [{ "type": "video", "url": "<https>" }],
  "publishNow": true
}
```

6. Trả JSON: `{ok, postpeer_id, tiktok_url, status, draft, credit_note}`. Không retry spam nếu 402 hết credit.

Caption: `_fb_plain_caption` tương đương — TikTok không markdown. Trần ~2200 ký tự; skill sẽ viết ngắn.

Cấm: `platforms` gồm facebook/instagram trong v1.

### 2.3 Brand kit

Thêm field **tùy chọn** vào kit (không bắt mọi page):

```
- TikTok accountId: acc_tt_...
- TikTok username: @tinhocsaoviet
```

Parse giống Page ID. Nhiều page Sao Việt **một** TK TikTok thương hiệu → ghi ở `_mac-dinh.md` hoặc `royce-shop.md`. Loop không xoay 50 page × 50 TikTok.

### 2.4 Skill + loop (giống FB, rút)

Skill mới `brains/Brain Default/skills/dang-video-tiktok/SKILL.md`:

- Video dọc 9:16, 15–60s (Reels/TT). Nguồn: URL CDN có sẵn **hoặc** file `attachments/dataset/...mp4` nếu public được.
- Caption 8–18 dòng: móc câu 1 dòng → 3 lợi ích → CTA ib/hotline kit **đúng cơ sở nếu video gắn cơ sở** → hashtag ≤ 5 (`#TinhocSaoViet #Excel #AI`).
- Cấm: x5, “5 phút”, nhồi AutoCAD+MISA vào video tin học, caption 40 dòng kiểu FB.
- 1 video = 1 thẻ (`tin-hoc_ai` / `do-hoa` / …).

Script `pick_next_tiktok.py` (copy tinh thần `pick_next_fanpage.py`):

- State `Javis/tiktok-queue.json`: 1 bài/ngày mặc định (credit).
- `NEXT=NONE` khi hết quota ngày hoặc chưa có `accountId` / chưa có video.
- `NEXT=1` → `account_id`, `caption_ctx`, `video_url`, `the`, `kit`.

Loop `Javis/loops/dang-video-tiktok-hang-ngay.md`:

- `enabled: false` mặc định.
- `mode: full`, `interval_min: 60` (không 5 phút — TikTok không cần xoay 50 page).
- 1 vòng: pick → (nếu cần) không spawn CLI nếu NEXT=NONE (zero-token: script in `NEXT=NONE`).
- Có NEXT: caption theo skill → `postpeer_tiktok_post` → `--ok`.
- `tools_profile: vault-safe` + tool postpeer danger chỉ khi full.

**Không** gọi `fb_page_*` trong loop này.

### 2.5 Test

`tests/python/test_postpeer_tiktok.py`:

- Mock httpx: list accounts, creator_info, post 200 → JSON ok.
- 402 hết credit → ERROR không retry.
- Thiếu key → `_check` tiếng Việt.
- `test_meta_pages.py` **không** đổi số tool Facebook.
- Catalog: id `postpeer` có `postpeer_tiktok_post` trong danger.

### 2.6 Docs

- `docs/09-mcp-va-so-lieu.md`: mục Kết nối TikTok PostPeer (5 bước OAuth trên site họ).
- `docs/29` hoặc đoạn trong ops: “TikTok v1 chưa vào /ops inbox”.
- README cuộc thi: “Fanpage = Graph tự host; TikTok = PostPeer BYO key (tùy chọn).”

---

## 3. Luồng 1 video (Gemini vẽ đúng cái này)

```
pick_next_tiktok.py
  NEXT=NONE → loop dừng, 0 LLM
  NEXT=1 account_id, video_url, the, kit
skill caption ngắn + CHAN_TRANG TikTok (hotline kit, không 12 cơ sở)
postpeer_tiktok_creator(account_id)
postpeer_tiktok_post(account_id, video, caption)
→ post_id / inbox draft
--ok ghi queue
```

Video mẫu user đã có: `https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/rendered_tin_hoc_ai_*.mp4` (HTTPS, 9:16) — dùng làm gold path v1 **không** cần upload.

---

## 4. PR

**PR 1 — Connector + plugin (MVP đăng tay qua chat Javis)**  
Catalog + plugin + test mock. Chủ: Kết nối key → Connect TikTok trên dashboard PostPeer → chat “đăng video này lên TikTok” với URL mẫu. Không loop.

**PR 2 — Skill + pick + loop**  
Queue 1/ngày, NEXT=NONE, enabled false. Caption skill. Không đụng loop Fanpage.

**PR 3 (không chặn thi)** — `postpeer_analytics` readonly + 1 thẻ `/ops` “TikTok 7 ngày” nếu còn bandwidth. Comments TikTok **cấm** hứa.

---

## 5. Cấm

- Không `platforms: facebook` qua PostPeer.
- Không lưu PostPeer key trong brand kit markdown (kit từng có Page Token — **đừng lặp** với PostPeer key).
- Không bật loop mặc định.
- Không đăng 50 clip/ngày (credit + spam TT).
- Không thay `tiktok-ads` MCP.
- Không rewrite `/ops` trừ PR 3.

---

## 6. Việc chủ làm trước khi Gemini test thật

1. Tài khoản PostPeer, copy access key.
2. Dashboard PostPeer → Connect TikTok (OAuth).
3. Kết nối Javis: trang Kết nối → TikTok (PostPeer) → dán key → nâng **Toàn quyền** khi muốn đăng.
4. Ghi `TikTok accountId` vào kit mặc định.
5. 1 URL video HTTPS 9:16 (CDN sẵn).

Gemini unit test **không** cần key. Live post chỉ khi chủ đưa URL + account.

---

## 7. Definition of done (PR 1+2)

Chat (console chủ, mode full): `postpeer_accounts` ra id; `postpeer_tiktok_post` với URL mẫu trả `ok` hoặc `draft=true` + không lộ key. Loop tắt. Fanpage Graph không đổi. Catalog + pytest mock xanh.
