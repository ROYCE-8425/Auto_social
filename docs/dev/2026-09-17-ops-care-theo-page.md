# Plan: Care theo từng page / nhóm brand + bật tắt từng chức năng

| Trường | Giá trị |
|---|---|
| **Cho** | Gemini implement |
| **Ngày** | 2026-09-17 |
| **Ảnh hiện trạng** | `/ops#overview`: banner cứng “Fanpage: Game Giá Rẻ BSN” + copy “giáo trình Sao Việt”; thẻ số **gom tất cả page**; không chọn page; không công tắc auto-reply comment / IB |
| **Cấm** | Sửa Graph plugin, PostPeer, classifier packs (trừ đọc `brand` đã có). Không bật `mode=full` mặc định. |

Đọc: `ops/src/pages/Overview.tsx`, `server/config.py` `fanpage_care.pages`, `server/fanpage_care.py` `poll_tick` / `process_inbound_*`, `fanpage_care_policy.py`.

---

## 0. Bệnh trên ảnh

1. **Một page giả làm cả hệ thống.** Hero “Fanpage: Game Giá Rẻ BSN” trong khi hộp thư lẫn Messenger + Facebook + (có thể) page khác. Copy “chuẩn bị câu trả lời theo giáo trình Sao Việt” **sai brand BSN**.
2. **Không có phạm vi.** Không chọn: *Tất cả page* / *chỉ BSN* / *chỉ Sao Việt* / *một Page ID*.
3. **Care = 1 công tắc + 1 mode.** Chủ muốn: tự rep comment **tách** tự IB Messenger, bật/tắt từng cái, từng page.
4. `settings.fanpage_care.pages` **đã có** `{}` nhưng UI `/ops` không ghi; poller chỉ đọc `pages.{id}.enabled` và `.mode`.

---

## 1. Mô hình cấu hình (không bịa key)

Mở rộng `fanpage_care` trong `settings.json` (default trong `config.py`):

```json
"fanpage_care": {
  "enabled": true,
  "mode": "suggest",
  "scope": "all",
  "scope_brand": "",
  "scope_page_id": "",
  "features": {
    "poll_comments": true,
    "poll_messenger": true,
    "auto_reply_comments": false,
    "auto_reply_messenger": false,
    "hide_spam": false,
    "crm": true,
    "drafts": true
  },
  "pages": {
    "343562028848465": {
      "enabled": true,
      "mode": "auto",
      "brand": "bsn",
      "features": {
        "auto_reply_comments": true,
        "auto_reply_messenger": false
      }
    }
  }
}
```

| Key | Ý nghĩa |
|---|---|
| `scope` | `all` \| `brand` \| `page` |
| `scope_brand` | `bsn` \| `saoviet` khi `scope=brand` |
| `scope_page_id` | Page ID khi `scope=page` |
| `features.*` | Công tắc **toàn cục**. Tắt = không chạy chức năng đó ở mọi page. |
| `pages.{id}` | Ghi đè: `enabled` false = bỏ page khỏi poll. `mode` chặt hơn global (policy hiện tại). `features` ghi đè từng bit. |

**Hợp nhất khi xử lý 1 comment/tin:**

```
page_on = pages[pid].enabled ?? true
feat_on(name) = pages[pid].features[name] ?? features[name] ?? default
mode_eff = effective_mode(global.mode, pages[pid].mode)
```

Poller: lọc `eligible_pages` theo `scope` rồi `pages[id].enabled`.  
`scope=brand` + `bsn` → chỉ kit `brand==bsn`.  
`scope=page` → đúng 1 id.

**Auto reply**

- `auto_reply_comments=false` → chỉ nháp (như suggest) dù `mode=auto`.
- `auto_reply_messenger=false` → không `fb_message_send`; vẫn ingest + CRM + nháp.
- Cả hai true **và** `mode` in (`auto`,`full`) mới gửi Graph.
- `mode=suggest` luôn nháp — công tắc auto **không** vượt suggest (an toàn). UI: disable công tắc auto kèm chữ “Đổi mode sang Tự FAQ / Tự động mới gửi”.

---

## 2. UI `/ops` (Overview + thanh lọc)

### 2.1 Thanh phạm vi (mọi trang: Overview, Hộp thư, CRM)

Hàng dưới nav:

```
Phạm vi: [ Tất cả page ] [ Brand: BSN ] [ Brand: Sao Việt ] [ Chọn 1 page ▾ ]
```

Ghi `POST /fanpage-care/settings` `{scope, scope_brand, scope_page_id}`.  
Inbox `getInbox` / stats / poll-now **lọc theo scope đang chọn** (query `page_id` hoặc `brand`).

Hero banner **bỏ cứng BSN + giáo trình Sao Việt**. Thay:

- Scope all: “Care · tất cả Fanpage đã nối”
- Scope brand bsn: “Care · Game Giá Rẻ BSN”
- Scope page: “Care · {tên page}”

### 2.2 Card “Chế độ Care” (owner + manager)

Thay khối “Trạng thái kết nối” một page:

| Công tắc | settings |
|---|---|
| Care tổng | `enabled` |
| Kéo comment | `features.poll_comments` |
| Kéo hộp thư IB | `features.poll_messenger` |
| Tự trả lời comment | `features.auto_reply_comments` (cần mode ≠ suggest) |
| Tự trả lời IB | `features.auto_reply_messenger` (cần mode ≠ suggest) |
| Ẩn spam (full) | `features.hide_spam` |
| Mode | suggest / auto / full (confirm khi rời suggest) |

Dưới: bảng **từng page eligible** (tên, brand chip BSN/Sao Việt, Page ID rút):

- Bật Care page  
- Mode page  
- Auto comment / Auto IB (checkbox)

`POST /fanpage-care/settings` merge vào `pages.{id}` — **không** xóa key khác.

Staff: **chỉ xem**, không ghi settings (RBAC hiện manager được `poll-now` + settings trừ full — giữ; staff 403 settings).

### 2.3 Hộp thư

Giữ nút Kéo comment / Kéo IB. Scope đang chọn = `page_id` gửi poll-now.  
Nháp hiện **tên page** (map `page_id` → eligible_pages.name), không chỉ Page ID.

---

## 3. Backend

`fanpage_care.py`

- `list_eligible_pages` đã có `brand`. Thêm helper `pages_in_scope(cfg, eligible) -> list`.
- `poll_tick`: lọc scope; nếu `features.poll_comments=false` thì `channel` không comments; `poll_messenger=false` thì không messenger.
- `process_inbound_comment`: trước gửi Graph, `feat_on("auto_reply_comments")` else draft.
- `process_inbound_message`: `feat_on("auto_reply_messenger")`.
- `GET /fanpage-care/state`: trả `scope`, `features`, `pages` (cắt token), `eligible_pages` đã lọc + **unfiltered count**.
- `GET /fanpage-care/inbox`: thêm `brand=bsn|saoviet` (lọc page_id thuộc kit brand). Stats theo cùng filter nếu query có.

`GET /fanpage-care/stats?brand=&page_id=` (optional): nếu inbox stats vẫn global, Overview **sai**. Phải đếm events 24h **theo scope**. Có thể lọc trong `get_stats(page_ids=...)`.

Test:

- `test_care_scope.py`: kit BSN + Q7; `scope=brand,b=bsn` → poll chỉ 343562028848465.
- `auto_reply_comments=false` + mode auto → không gọi `fb_page_reply`.
- `auto_reply_messenger=false` → không `fb_message_send`.
- Settings merge pages không xóa page khác.

---

## 4. Copy tiếng Việt

- Tất cả page  
- Nhóm Game BSN  
- Nhóm Sao Việt  
- Một Fanpage  
- Tự trả lời bình luận  
- Tự trả lời tin nhắn (IB)  
- Kéo comment / Kéo hộp thư IB  
- “Mode Chỉ nháp: công tắc tự trả lời không gửi ra Facebook.”

Cấm: “giáo trình Sao Việt” trên banner BSN.

---

## 5. PR

**P1** — Schema settings + `pages_in_scope` + stats theo page_ids + test.  
**P2** — Poller + process_* tôn trọng features.  
**P3** — Overview: scope bar, banner đúng, card công tắc, bảng per-page.  
**P4** — Inbox/CRM lọc theo scope; tên page trên nháp.

Definition of done: chọn “Nhóm Game BSN” → số 24h/nháp **chỉ BSN**; tắt “Tự trả lời IB” → vẫn kéo tin Quốc Khánh, **không** `fb_message_send`; bật auto + mode auto → FAQ/lead gửi. Sao Việt không nhận template BSN (đã có classifier).

Mặc định ship: `scope=all`, `auto_reply_*=false`, `mode=suggest` — giống hiện tại (nháp). Chủ tự bật từng page.
