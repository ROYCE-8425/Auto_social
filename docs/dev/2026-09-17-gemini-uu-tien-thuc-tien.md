# PROMPT GEMINI — Ưu tiên thực tiễn (không thêm kênh mới)

Dán từ **BẮT ĐẦU** đến **HẾT**. Đọc mục 0–1 trước. Code theo P0 → P1. **Cấm** Instagram, Zalo, Ads, “AI viral”, fake chart.

Repo: Auto_social / Javis OS. Live: `https://trannhuy.online/ops` và `/app`.

---

## BẮT ĐẦU

### 0. Đã có — CẤM viết lại

- `/ops` RBAC, landing `/`, console `/app`
- Care: poll comment + IB, CRM, classifier BSN ≠ Sao Việt
- Phạm vi: Tất cả / Nhóm BSN / Nhóm Sao Việt / 1 page (`pages_in_scope`, `fanpage_care.features`)
- Tổng quan 2 cột: bình luận chờ / tin IB chờ
- API `GET /fanpage-care/inbox?kind=comment|message`
- TikTok: plugin PostPeer (`postpeer_tiktok_post`, `postpeer_tiktok_photos`), `/tiktok/status`, `/tiktok/post`, `/tiktok-media/`, trang `/app` TikTok + `/ops` Kênh TikTok chỉ xem
- Kit BSN: Page `343562028848465`, TikTok `accountId=6aa3ba9df4c58f3c57921507` `@seotrum`
- Key PostPeer: MCP `STATE_DIR` qua `scripts/connect_postpeer.py`. **Cấm** ghi key vào kit/git.

### 1. Hiện trạng thật (ảnh `/ops`)

| Ổn | Hỏng / dở |
|---|---|
| Tách 3 comment vs 13 IB trên Tổng quan | TikTok UI: có `@seotrum` nhưng badge **Chưa nối**, 0 nick, “key chưa cấu hình” (VPS **chưa** chạy connect_postpeer) |
| Phạm vi BSN | Chưa **một lần đăng TikTok live** từ nút Đăng thử |
| Comment BSN vào nháp | Inbox từng gọi hết rồi heuristic `target_id`; phải `kind=` trên từng tab |
| | Xu hướng từng **bịa** Q10 / 28.5% / random — đã cấm fallback giả |
| | Acc TikTok là **@seotrum** không phải shop BSN — UI phải nói thẳng |

**Không thiếu sản phẩm.** Thiếu: luồng đóng, số thật, 1 bài TikTok ra app.

---

## P0 — Đóng luồng đang hở (làm hết trước feature mới)

### P0.1 Inbox & Overview chỉ tin `events.kind`

- `Inbox.loadData`: tab comments → `getInbox({ kind: 'comment' })`; tab IB → `kind: 'message'` + conversations.
- **Xóa** heuristic `target_id.length` / `includes('_')`.
- Draft không join event.kind → **không** hiện tab comment.
- Pytest: 1 comment + 1 message draft → mỗi kind đúng 1.
- Tab copy: `Bình luận bài viết (N chờ)` / `Tin nhắn IB (M chờ)` — cấm “0 · 13 gợi ý”.

### P0.2 TikTok trạng thái không mâu thuẫn

`GET /tiktok/status`:

- `connected` = có `postpeer_key` trong MCP.
- `accounts` = API PostPeer (rỗng nếu chưa key trên **đúng VPS**).
- UI: `connected` → “Đã lưu key …xxxx”; không thì “Chưa dán key — chủ máy /app”.
- **Cấm** hardcode `@seotrum` khi `accounts=[]`.
- Loop: chữ “Đăng 1 carousel/ngày”, không slug file.
- `/ops` không nút đăng (staff 403 `POST /tiktok/post`).

Vận hành (ghi trong README `/app` TikTok, không hardcode key):

```
POSTPEER_API_KEY='…' python scripts/connect_postpeer.py
systemctl restart javis
```

### P0.3 Một lần **Đăng thử thành công**

Từ `/app` → TikTok:

1. 4 ảnh từ `attachments/dataset/game-bsn/<một game>/` crop 1080×1920 → `_xuat-tiktok/bsn/`.
2. Public `https://trannhuy.online/tiktok-media/bsn/...` (GET **và** HEAD 200, không cookie — PostPeer phải tải được).
3. `postpeer_tiktok_photos` + `autoAddMusic`.
4. Dòng `Javis/tiktok-posts.jsonl` + hiện trên `/ops` Kênh TikTok.
5. Bài hoặc **nháp inbox TikTok** (`draft=true` cũng là thành công — ghi rõ trên UI).

Nếu 401/404 media: sửa route, đừng fake “đã đăng”.  
Nếu PostPeer 401: key chưa trên VPS, đừng giả accounts.

### P0.4 Công tắc Care phải **có tác dụng**

`features.auto_reply_comments` / `auto_reply_messenger` + `mode=suggest` → **không** Graph.  
Tắt IB auto → vẫn kéo tin, chỉ nháp.  
Test `test_care_scope.py` / policy: mode suggest + auto_reply true → vẫn draft.

UI Tổng quan: khi suggest, disable công tắc tự gửi, chữ “Đổi mode Tự FAQ mới gửi ra Facebook”.

---

## P1 — Đáng làm, nhỏ, phục vụ vận hành

1. **Tên page trên mọi nháp** (đã có BSN) — đủ; ẩn `Target: 12218…` với nhân viên.
2. **Gửi nháp từ Tổng quan** đã có nút — đảm bảo comment → `fb_page_reply`, IB → `fb_message_send` (test 2 nhánh).
3. **Token Page BSN** thiếu `pages_messaging` thì kéo IB lỗi — UI pollHint hiện nguyên message Graph, hướng dẫn “cần quyền Messenger trên Page Token”.
4. **Kit BSN**: không quote “12.000+ khách hàng” thành học phí (đã có skip; gold test comment “uy tín” / “check ib”).
5. **50 page Sao Việt**: `list_eligible_pages` phải đếm đúng kit có Page ID. Chip “Tất cả page 2” là **sai** nếu vault có hàng chục kit — sửa parser/đếm, đừng hardcode 2.

---

## P2 — Chỉ khi P0 xong (không chặn thi)

- Webhook HTTPS (poll đủ demo).
- App Review Messenger Live.
- Connect acc TikTok **shop BSN** trên PostPeer (thay @seotrum) — việc chủ, Gemini chỉ cho ô accountId kit.
- Loop TikTok `enabled: true` **sau** 3 lần Đăng thử ổn. Mặc định false.
- Ảnh AI portrait → `_xuat-tiktok` — phụ; dataset BSN đã có 6 ảnh/game.

---

## Cấm (không phải “thiếu tính năng”)

- Instagram, YouTube, Zalo, Shopee, Ads.
- Chat Javis trong `/ops`.
- Facebook qua PostPeer.
- Chọn 1 bài nhạc trend (API không có) — chỉ `autoAddMusic`.
- Fake chart, fake “Đã đăng”, fake 28% lead.
- Bật `mode=full` mặc định.
- Commit PostPeer key / Page token.

---

## Definition of done (thực tế)

Checklist chủ máy:

- [ ] `/ops` Tổng quan: 2 cột, không lẫn IB vào comment.
- [ ] Tab comment không có “Jurassic World…”; tab IB không có Trần Như Ý.
- [ ] `/ops` TikTok: key đúng trạng thái VPS; không “Chưa nối” khi đã có …xxxx.
- [ ] `/app` Đăng thử → jsonl + media 200 + PostPeer không 401.
- [ ] Staff 403 `/tiktok/post`.
- [ ] Tắt tự IB: không `fb_message_send`.
- [ ] Pytest: kind split, care features, tiktok studio, **không** test live Graph.

## HẾT

---

Thứ tự commit: P0.1 → P0.2 → P0.3 (live) → P0.4 → P1. Không mở PR “tính năng mới” khi P0.3 chưa có 1 bài TikTok thật.
