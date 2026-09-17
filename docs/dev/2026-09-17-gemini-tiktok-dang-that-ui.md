# PROMPT GEMINI — Đăng TikTok thật + UI `/app` & `/ops` + thư mục Javis

Copy từ dòng **BẮT ĐẦU PROMPT** đến hết **Definition of done**. Đọc mục 0 trước khi code. Không bịa API. Không commit PostPeer key.

---

## BẮT ĐẦU PROMPT

Bạn đang làm trên repo Auto_social (Javis OS fork). Nhiệm vụ: **đăng TikTok thật** (carousel ảnh 9:16 + nhạc auto), **giống loop Fanpage**, có **UI quản lý trên `/app` (chủ máy) và `/ops` (nhân viên xem, không cầm key)**, và **thư mục vault chuẩn cho Javis**.

### 0. Đã có — đừng làm lại / đừng phá

- Plugin `system/plugins/postpeer-tiktok/`: `postpeer_accounts`, `postpeer_tiktok_creator`, `postpeer_tiktok_post` (video URL), **`postpeer_tiktok_photos`** (ảnh URL + `autoAddMusic`).
- Connector catalog `postpeer` (apikey `postpeer_key`). Key lưu MCP `STATE_DIR`, **cấm** brand kit / git.
- Script `scripts/connect_postpeer.py` (env `POSTPEER_API_KEY`).
- Kit `game-gia-re-bsn.md`: Kênh TikTok **Bật: true**, `accountId=6aa3ba9df4c58f3c57921507`, username **`@seotrum`** (acc đang Connect trên PostPeer — không phải @gamegiarebsn).
- Loop `dang-video-tiktok-hang-ngay.md` **`enabled: false`**.
- Fanpage Graph **không** đi PostPeer.
- Care comment/IB **không** đụng trong PR này.

Nhạc: **`autoAddMusic=true`**. API **không** chọn 1 bài trend cụ thể. UI ghi rõ: “TikTok tự gắn nhạc gợi ý”.

Ảnh: PostPeer **bắt buộc URL https**. File local không đăng được trừ khi server **public** được file đó.

### 1. Thư mục Javis (tạo thật, README 10 dòng)

Trong vault `brains/Brain Default/`:

```
attachments/dataset/_xuat-tiktok/     # ảnh/video 9:16 SẴN SÀNG đăng (output AI + crop)
attachments/dataset/_xuat-tiktok/bsn/
attachments/dataset/_xuat-tiktok/saoviet/
attachments/dataset/tiktok-queue/     # không bắt buộc; queue JSON đã ở Javis/tiktok-queue.json
Javis/tiktok-posts.jsonl              # log mỗi lần đăng: ts, kit, accountId, postpeer_id, urls, caption, status
```

Không nhét key vào đây. `_xuat-tiktok` gitignore ảnh lớn nếu cần; **giữ** `.gitkeep` + README.

### 2. Public HTTPS cho file vault (bắt buộc, nếu không không đăng được)

Thêm route **chỉ owner** (cookie Javis `/app`, không staff `/ops`):

`GET /tiktok-media/{rel}`  
- `rel` chỉ dưới `attachments/dataset/_xuat-tiktok/` (chống `..`).  
- Content-Type jpeg/png/mp4.  
- Trả file bytes.

Base public: `https://trannhuy.online/tiktok-media/bsn/foo.jpg` (cùng origin app).  
Poller/tool dựng URL tuyệt đối từ `Host` / settings `domain.custom`.

Test: file `.gitkeep` hoặc 1 jpeg test → GET 200; path `../wiki` → 404.

**Staff `/ops` không upload, không thấy URL thô nếu không cần.** Chủ `/app` thấy preview.

### 3. Pipeline đăng (na ná `fb_page_album`)

Một “lượt đăng TikTok” (chat `/app` hoặc nút UI hoặc loop):

1. Chọn kit có `Kênh TikTok.Bật` + `accountId` ≠ `CHƯA_NỐI`.
2. Nguồn ảnh (theo thứ tự, UI chọn):
   - **Dataset sẵn:** 4–6 file 9:16 từ `attachments/dataset/game-bsn/<game>/` (BSN) hoặc `tin-hoc_ai/` (Sao Việt) — **crop/copy** sang `_xuat-tiktok/{brand}/` nếu chưa 9:16 (Pillow: cover 1080×1920, không méo logo quá 15%).
   - **AI:** `javis_generate_image` `aspect_ratio=portrait` (prompt bám kit: BSN = poster game, cấm giáo trình Sao Việt). Lưu `_xuat-tiktok/{brand}/`.
3. Đổi path → URL public `/tiktok-media/...`.
4. Caption 8–18 dòng từ skill `dang-video-tiktok` / khối kit TikTok (hashtag, hotline **đúng brand**).
5. `postpeer_tiktok_photos(account_id, images=[urls], caption, auto_add_music=true, disable_duet/stitch từ kit)`.
6. Ghi `Javis/tiktok-posts.jsonl`. Hiện `status` + `tiktok_url` hoặc `draft=true` (inbox TikTok).

Loop: 1 bài/ngày, `enabled: false` mặc định. Nút UI **Đăng thử ngay** = 1 lượt, `mode=full` + connection perm full.

### 4. UI `/app` (dashboard Alpine, chủ máy)

Trang mới **TikTok** trong nhóm Kết nối (`console.js` RAIL + `dashboard/tiktok-studio.js` + CSS).

Khối:

1. **Kết nối:** trạng thái PostPeer (đã nối / thiếu key). Nút “Mở Kết nối MCP” → `mcp`. Không hiện full key; chỉ `…xxxx`. `postpeer_accounts` → bảng @username + accountId. Nút “Ghi accountId vào kit đang chọn”.
2. **Kit:** dropdown brand kits có khối TikTok. Hiện Bật, @user, hashtag. Sửa Bật / accountId (ghi markdown kit) — **không** ô access key.
3. **Hàng đợi / đăng thử:** chọn nguồn Dataset | AI; số ảnh 4–6; preview 9:16; caption textarea (prefill skill); checkbox “Nhạc auto”; nút **Đăng thử** (confirm). Log 20 dòng từ jsonl.
4. **Thư mục:** list file `_xuat-tiktok/` + upload ảnh 9:16 (owner). Upload vào đúng brand subfolder.
5. **Loop:** hiện `enabled` loop `dang-video-tiktok-hang-ngay`; toggle ghi file loop yaml (cùng cơ chế loop UI hiện có nếu có; không invent runner mới).

i18n vi: `TikTok đăng bài`. Cache-bust `tiktok-studio.js?v=`.

### 5. UI `/ops` (nhân viên)

**Không** PostPeer key, **không** Đăng thử.

Trang hoặc tab **TikTok** (manager+owner xem; staff xem read-only):

- Acc đang dùng (@seotrum), kit BSN/Sao Việt.
- 10 bài gần nhất từ jsonl: giờ, caption rút, status, link TikTok nếu có.
- Trạng thái loop (bật/tắt) — **chỉ owner** bật; staff thấy chữ “Chủ máy bật trên /app”.
- Không upload, không gen AI.

RBAC: `GET /tiktok/status` staff ok; `POST /tiktok/post` owner only (403 staff). Media GET: owner session `/app` (cookie javis), không `ops_session`.

### 6. API (mỏng, không Graph)

| Method | Path | Ai | Việc |
|---|---|---|---|
| GET | `/tiktok/status` | ops + owner | accounts ẩn key, kit tiktok, last 10 jsonl, loop enabled |
| POST | `/tiktok/post` | owner | body `{kit_file, source: dataset\|ai, count, caption?}` chạy 1 lượt |
| POST | `/tiktok/upload` | owner | multipart → `_xuat-tiktok/{brand}/` |
| GET | `/tiktok-media/{rel}` | public **hoặc** signed? | **Ưu tiên:** public read-only trên prefix `_xuat-tiktok` (cần PostPeer fetch). Không list directory. |

Nếu ngại public: token query 1h. PostPeer phải GET được không cookie. **Public prefix hẹp là đúng.**

### 7. Test

- Catalog có `postpeer_tiktok_photos` danger.
- Media path traversal 404.
- POST `/tiktok/post` staff 403.
- Mock PostPeer 200 → jsonl 1 dòng.
- Picker kit BSN → account `@seotrum`.
- Không assert đăng live trong CI.

### 8. Deploy VPS

- `POSTPEER_API_KEY` trên VPS: `python scripts/connect_postpeer.py` (key user tự export; **cấm** hardcode trong repo).
- Restart `javis.service`.
- Definition of done **live:** từ `/app` → TikTok → Đăng thử 4 ảnh dataset BSN 9:16 → PostPeer 200 hoặc `draft=true` hiện trên UI. `/ops` thấy dòng log. TikTok app/@seotrum có bài hoặc inbox nháp.

### 9. Cấm

- Key trong markdown/kit/commit.
- Facebook qua PostPeer.
- Bật loop mặc định.
- “Đã đăng” khi chỉ mock UI.
- Nhạc = file mp3 tự mix (v1 không làm). Chỉ `autoAddMusic`.
- Staff 403 `/tiktok/post`.

## HẾT PROMPT

---

## Ghi chú cho bạn (không dán Gemini)

Acc TikTok đang Connect là **@seotrum**, không phải shop BSN. Muốn brand BSN: Connect acc shop trên postpeer.dev rồi dán `accountId` mới vào kit.

Ảnh AI xong vẫn phải nằm `_xuat-tiktok/` và URL `/tiktok-media/...` public thì PostPeer mới kéo được.
