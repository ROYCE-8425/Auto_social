# Plan: TikTok thành kênh thật (kit + nền tảng trên hộp thư) — không giả Care Graph

| Trường | Giá trị |
|---|---|
| **Cho** | Gemini implement |
| **Ngày** | 2026-09-17 |
| **Vấn đề** | Kit / Care / `/ops` đang **chỉ Fanpage**. TikTok mới có plugin đăng video, chưa có kit kênh, chưa gắn `platform` lên sự kiện. |
| **Cấm** | Đưa Facebook qua PostPeer. Bịa API comment TikTok nếu PostPeer không trả comment. Trộn caption 40 dòng FB vào TikTok. |

Đọc trước: `docs/dev/2026-09-16-postpeer-tiktok-plan.md` (đăng video). Plan này **bổ sung kênh**, không viết lại plugin đăng.

---

## 0. Hiện trạng (đừng sửa nhầm)

| Thành phần | Facebook | TikTok hôm nay |
|---|---|---|
| Brand kit | 1 file / Fanpage (`Page ID`, album 1:1, chân trang dài, 13 cơ sở) | Skill đọc `TikTok accountId` nếu có — **hầu hết kit không có khối kênh** |
| Đăng | `fb_page_album` / Graph | `postpeer_tiktok_post` (URL https) |
| Care comment | poll Graph + classifier `hoc_phi/dia_chi` | **Không ingest** |
| Event store | `kind=comment\|message`, `page_id` | **Không cột `platform`** → UI không biết kênh |
| `/ops` Hộp thư | Tab “Bình luận Fanpage” / Messenger | Không chip, không lọc TikTok |
| Classifier | Keyword đào tạo (Excel, MISA, AutoCAD) | Không pack Game BSN (`steam`, `key`, `bảo hành`) |
| Brand | Sao Việt + kit `game-gia-re-bsn.md` | Loop TikTok vẫn caption **tin học** |

Hệ quả: đăng TikTok (nếu có) vẫn “nói như Fanpage Sao Việt”; hộp thư không ghi **nền tảng**.

---

## 1. Nguyên tắc kênh

1. **Một file kit = một thương hiệu** (Sao Việt cơ sở X, hoặc Game BSN). Không clone 50 file TikTok.
2. Kit có **khối kênh** bắt buộc parse:

```markdown
## Kênh Facebook
- Bật: true
- Page ID: 988656934325292
- Tỷ lệ ảnh: 1:1
- Caption: dài (album)

## Kênh TikTok
- Bật: true
- accountId: acc_tt_xxxxx
- username: @tinhocsaoviet
- Tỷ lệ: 9:16
- Caption: ngắn (8–18 dòng)
- Hashtag: #TinhocSaoViet #HocExcel
- Tắt Duet: true
- Tắt Stitch: true
- Video CDN: https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/
```

3. Parser Python dùng chung: `server/brand_kit.py` (mới). Trả `KitChannel{platform, enabled, ids, caption_mode, extras}`. Loop FB **bỏ qua** kênh TikTok; loop TT **bỏ qua** nếu `Bật: false` hoặc thiếu `accountId`.
4. `platform` trên mọi sự kiện Care: `'facebook' | 'tiktok' | 'messenger'`. Messenger = Facebook inbox (giữ). Không nhét `'postpeer'` vào UI.

---

## 2. Việc Gemini **phải** làm (thứ tự PR)

### PR T1 — Parser kit đa kênh + điền kit mẫu

**File**

- `server/brand_kit.py` — parse `## Kênh Facebook` / `## Kênh TikTok` (không phân biệt hoa thường). Thiếu khối → Facebook: suy từ `Page ID:` cũ (tương thích kit hiện tại). TikTok: `enabled=false`.
- Test `tests/python/test_brand_kit_channels.py`: kit chỉ Page ID → facebook on, tiktok off; kit đủ 2 khối → cả hai.
- Sửa **2 kit mẫu**, không đụng 50 file campus trừ khi có sẵn username:
  - `wiki/brand-kits/_mac-dinh.md` + `royce-shop.md`: thêm `## Kênh TikTok` (accountId để trống `CHƯA_NỐI`, Bật: false cho đến khi chủ dán id).
  - `wiki/brand-kits/game-gia-re-bsn.md`: khối TikTok riêng (hashtag gaming, **cấm** copy USP đào tạo).

**Cấm** ghi PostPeer key vào kit.

### PR T2 — `platform` trên store + API

`fanpage_care_store.py`:

- `ALTER` / tạo cột `events.platform TEXT NOT NULL DEFAULT 'facebook'`.
- Index `(platform, created_ts)`.
- `insert_event(..., platform='facebook')`.
- `list_events(platform=None)` filter.

`GET /fanpage-care/inbox?platform=facebook|tiktok` (optional). Mỗi event JSON **bắt buộc** `"platform"`.

Poller Graph hiện tại: luôn `platform='facebook'`.

`/ops` Inbox + Overview:

- Chip màu: **Facebook** (xanh Meta) / **TikTok** (đen) / **Messenger**.
- Lọc “Mọi nền tảng | Facebook | TikTok”.
- Tab hiện tại đổi nhãn: “Bình luận” (không cứng “Fanpage”); Messenger giữ.

Test: insert facebook + tiktok → list filter đúng; UI type `CareEvent.platform`.

**Không** bịa field khác.

### PR T3 — Classifier theo **brand + platform**

`fanpage_care_classify.py` giữ rules-first.

Thêm pack:

| Pack | Dùng khi |
|---|---|
| `core` | spam/toxic/phone (mọi kênh) |
| `saoviet_fb` | `hoc_phi`, `dia_chi`, `lich_hoc` (như hiện tại) |
| `saoviet_tt` | FAQ ngắn: “link bio”, “ib học”, ít địa chỉ (1 cơ sở hoặc “xem bio”) |
| `bsn_fb` / `bsn_tt` | `mua key`, `steam`, `offline`, `bao hanh`, `viet hoa` — **không** map Excel/MISA |

`classify_comment(text, *, platform='facebook', brand='saoviet')`.

Brand suy từ kit file stem (`game-gia-re-bsn` → `bsn`, còn lại `saoviet`) hoặc tag kit.

Gold tests: comment “học phí Q7” → saoviet_fb `hoc_phi`; “key steam bảo hành” → bsn; “ib bio” → saoviet_tt không bịa 13 chi nhánh.

### PR T4 — Đăng TikTok **đọc kit kênh** (không đọc chân trang FB)

Sửa skill `dang-video-tiktok/SKILL.md` + `pick_next_tiktok.py`:

- Chỉ chọn kit `Kênh TikTok.Bật: true` và `accountId` không `CHƯA_NỐI`.
- Caption từ khối TikTok (hashtag, tắt Duet), **cấm** dán `CHAN_TRANG` 13 cơ sở.
- Game BSN vs Sao Việt: `the` / folder video **không** dùng `attachments/dataset/tin-hoc` cho kit BSN.

Loop vẫn `enabled: false`.

Test script: kit thiếu TikTok → `NEXT=NONE no_tiktok_channel`.

### PR T5 — Comment TikTok: **thật hoặc ghi rõ không có**

Gemini **mở docs PostPeer Comments** lúc code.

- Nếu API **có** list comment theo `accountId` TikTok: tool `postpeer_tiktok_comments` (readonly) + worker nhẹ (interval ≥ 15 phút, cap 20 video) → `insert_event(platform='tiktok')`. Trả lời comment TikTok **v1 chỉ nháp** (`drafts`), **không** auto-reply công khai (policy + API yếu).
- Nếu API **không** list comment TikTok: **không** giả ingest. `/ops` khi lọc TikTok: empty state *“PostPeer chưa đọc comment TikTok. Kênh này mới đăng video.”* Test snapshot empty.

Cấm viết crawler web TikTok / cookie.

---

## 3. Việc **không** làm trong đợt này

- 50 tài khoản TikTok = 50 Fanpage.
- Care Messenger TikTok (DM) — phase sau.
- Analytics views trên `/ops` Xu hướng — sau khi có ≥1 bài live.
- Đổi landing (đang kể Sao Việt) trừ 1 dòng “đa kênh Facebook / TikTok” nếu sửa `website/index.html` (optional, 1 câu).
- Sửa Graph plugin.

---

## 4. UI copy (đúng chữ)

- Chip: `Facebook` · `TikTok` · `Messenger`
- Lọc: `Nền tảng`
- Empty TikTok (khi chưa API comment): `Chưa có bình luận TikTok — kênh này dùng để đăng video.`
- Kit thiếu accountId: loop `NEXT=NONE chua-noi-tiktok`

---

## 5. Kiểm thử

```
python -m pytest tests/python/test_brand_kit_channels.py tests/python/test_fanpage_care_classify.py tests/python/test_postpeer_tiktok.py tests/python/test_fanpage_care_store.py
```

Thủ công `/ops` Hộp thư: comment FB có chip Facebook. Không bịa dòng TikTok.

---

## 6. Definition of done

1. Parser đọc `## Kênh TikTok` / Facebook; kit cũ không gãy.
2. Mọi event Care có `platform`; `/ops` lọc + chip.
3. Classifier BSN ≠ Sao Việt; TikTok ≠ chân trang 13 cơ sở.
4. Loop TikTok chỉ chạy kit đã bật kênh + accountId.
5. Comment TikTok: API thật **hoặc** empty trung thực — không event giả.

Chủ máy sau PR: dán `accountId` vào kit, `Bật: true`, Kết nối PostPeer Toàn quyền — mới đăng được. Gemini không bật loop.
