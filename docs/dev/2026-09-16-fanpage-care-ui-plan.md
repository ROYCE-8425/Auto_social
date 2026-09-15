# Plan UI/UX: trang Chăm sóc Fanpage không còn “một cục”

| Trường | Giá trị |
| --- | --- |
| **Trạng thái** | Plan cho Gemini implement (không đổi policy Care) |
| **Ngày** | 2026-09-16 |
| **Ảnh hiện trạng** | VPS `http://180.93.37.8:7777` — Care tắt, Facebook báo `readonly`, bảng trống |
| **Phạm vi** | `dashboard/fanpage-care.js`, `dashboard/console.css`, cache bump `index.html`, **một** sửa backend: đọc perm Facebook đúng chỗ |

---

## 1. Bệnh trên ảnh (phải chữa đúng cái này)

Trang **Chăm sóc Fanpage** hiện là **một khối điều khiển dồn** rồi một bảng rỗng. Người dùng không biết phải làm gì tiếp.

Cụ thể trên screenshot:

1. Banner vàng “Kết nối Facebook đang ở chế độ `readonly`” — **không có nút** đi tới trang Kết nối.
2. Checkbox native “Đang tắt Care” + dropdown `suggest (Gợi ý nháp, duyệt tay)` + pill giờ im lặng + `Quét ngay` + `Kill Switch` **cùng một hàng/cột**, không phân cấp.
3. Ba “tab” trông như nút xám hệ thống dính nhau: *Bình luận & Bản nháp / Messenger Development / Khách hàng (CRM)*.
4. Hai dropdown `-- Mọi Fanpage --` / `-- Mọi phân loại --` rồi bảng 6 cột với đúng một dòng *“Chưa có bình luận nào trong 24 giờ qua.”*
5. Không có checklist “bật Care thì sao”, không có số liệu (bao nhiêu page / nháp / lead), không empty state hướng dẫn comment thử.
6. Tab Messenger trong code **còn chữ “Sẵn sàng ở bản cập nhật tiếp theo”** trong khi backend đã có `GET /fanpage-care/conversations` + takeover — UI nói dối.
7. CSS Care nằm ở `console.css` nhưng `index.html` vẫn `console.css?v=68` và `fanpage-care.js?v=1`. VPS cache file cũ → toggle/tab **không ra style** (ảnh đúng kiểu HTML trần).

**Không** nằm trong PR này: đổi policy suggest/auto/full, Graph tools, classifier, CRM schema.

---

## 2. Bug backend bắt buộc (1 hàm)

`GET /fanpage-care/state` đang làm:

```python
import mcp_catalog
conn = mcp_catalog.get_connection("facebook-pages")  # HÀM NÀY KHÔNG TỒN TẠI
```

`except` nuốt lỗi → `connection_perm` **luôn** `"readonly"` dù user đã nâng Toàn quyền. Banner vàng trên ảnh có thể là **false positive**.

Sửa trong `server/fanpage_care.py`:

```python
def facebook_pages_status() -> dict:
    """Fail-closed: chưa nối → connected=False, perm=readonly.
    Đọc mcp_store.list_connections() theo connector_id == 'facebook-pages'.
    Nếu có nhiều connection: ưu tiên cái perm=='full' đang enabled.
    """
```

Trả thêm trong `/fanpage-care/state`:

- `connection_perm`: `readonly` | `full`
- `facebook_connected`: bool
- `facebook_label`: tên connection

Test: `tests/python/test_fanpage_care_state_perm.py` (monkeypatch `mcp_store.list_connections`):

| Fixture | Kỳ vọng |
| --- | --- |
| `[]` | `connected=False`, `perm=readonly` |
| `[{connector_id: facebook-pages, enabled: True, perm: full}]` | `connected=True`, `perm=full` |
| `[{connector_id: facebook-pages, perm: readonly}]` | `connected=True`, `perm=readonly` |
| `mcp_catalog.get_connection` không được gọi | (assert not called) |

---

## 3. Bố cục đích (một màn, 4 tầng)

```
┌─────────────────────────────────────────────────────────┐
│ A. CHECKLIST (chỉ hiện khi chưa sẵn sàng)               │
│  ① Facebook  [đủ / thiếu]     [Mở Kết nối →]            │
│  ② Bật Care  [đang tắt/bật]                             │
│  ③ Quét thử  [Chưa có bình luận] [Quét ngay]            │
├─────────────────────────────────────────────────────────┤
│ B. 4 THẺ SỐ  Page kit | Bình luận 24h | Nháp | Lead/CRM │
├─────────────────────────────────────────────────────────┤
│ C. THANH ĐIỀU KHIỂN                                     │
│  [toggle Care]  [Chỉ nháp|Tự FAQ|Tự động+tin]           │
│  [Quét ngay]                    [Dừng gửi — Kill]       │
│  pill: giờ im lặng / quyền Facebook                     │
├─────────────────────────────────────────────────────────┤
│ D. TAB gạch chân                                        │
│  Bình luận (n) | Messenger | Khách hàng (n)             │
│  … nội dung tab (thẻ, không bảng rỗng)                  │
└─────────────────────────────────────────────────────────┘
```

Kill Switch **không** đứng cạnh Quét ngay như hai nút ngang hàng. Quét = primary. Kill = chữ/nút phụ bên phải, đỏ nhạt.

---

## 4. Tầng A — Checklist 3 bước

Hiện khi **một** trong: `!facebook_connected` hoặc `perm != full` hoặc `!enabled` hoặc `events_24h == 0`.

Ẩn hoàn toàn khi cả 3 xong **và** đã có ≥1 event (user đã qua lần đầu).

| Bước | Done khi | Copy + CTA |
| --- | --- | --- |
| 1. Facebook Toàn quyền | `facebook_connected && perm==full` | Thiếu: “Vào Kết nối, thẻ Facebook Trang → Kết nối lại / nâng Toàn quyền.” Nút **Mở Kết nối** gọi `window.JavisNav.go("mcp")`. |
| 2. Bật Care | `config.enabled` | “Công tắc bên dưới. Lần đầu để **Chỉ nháp** — không gửi ra Facebook.” |
| 3. Có dữ liệu | `stats.events_24h > 0` | “Bấm **Quét ngay**. Hoặc comment thử trên 1 Fanpage (cơ sở ở đâu / học phí / để SĐT).” |

Mỗi bước: vòng tròn số / dấu check, 1–2 câu, 1 nút. Không paragraph.

Banner `readonly` cũ **thay** bằng bước 1 (không lặp chữ).

Kill switch đang bật: banner đỏ riêng phía trên checklist, copy: “Đã dừng mọi lệnh gửi. Vẫn nhận bình luận và CRM.”

---

## 5. Tầng B — 4 thẻ số

Lấy từ `state.stats` + `eligible_pages.length` (API đã có: `events_24h`, `pending_drafts`, `leads_24h`, `total_customers`).

| Thẻ | Số | Click |
| --- | --- | --- |
| Fanpage có kit | `eligible_pages.length` | không |
| Bình luận 24h | `events_24h` | tab Bình luận |
| Nháp chờ duyệt | `pending_drafts` | tab Bình luận, cuộn tới nháp |
| Khách / lead | `total_customers` + `leads_24h` nhỏ | tab Khách |

Thẻ 1 hàng, mobile 2×2. Số to, nhãn nhỏ.

---

## 6. Tầng C — Điều khiển

**Toggle Care:** slider CSS (đã có `.care-toggle`) + nhãn **Đang tắt** / **Đang bật — Chỉ nháp** / **Đang bật — Tự FAQ** / **Đang bật — Tự động**.

**Mode = 3 nút segment**, bỏ `<select>` jargon:

| value | Nhãn nút | Dòng phụ khi chọn |
| --- | --- | --- |
| `suggest` | Chỉ nháp | Không gửi Facebook. Bạn bấm Gửi trên từng nháp. |
| `auto` | Tự FAQ | Tự trả lời comment học phí/địa chỉ/lịch. Không Messenger. |
| `full` | Tự động + tin | FAQ + AI câu khó + Messenger (cửa sổ 24h). |

Confirm khi rời `suggest` **và** `perm==full` (copy hiện có). Nếu `perm!=full`, chọn `auto`/`full` vẫn lưu nhưng banner bước 1 nói rõ **chưa gửi được** cho đến khi Toàn quyền.

**Quét ngay:** primary. Khi bấm: disable + “Đang quét…”. Nếu API `result.status==skipped` (`disabled` / `no_eligible_pages`) → toast/alert đúng lý do, không im.

**Kill Switch:** phụ, không cùng visual weight. Bật: confirm. Đang bật: nút đặc đỏ “Đang dừng gửi — bấm để mở lại”.

**Giờ im lặng:** pill, không phải control. Tooltip: 21h–7h không gửi, vẫn ghi CRM.

---

## 7. Tầng D — Tab

CSS tab **gạch chân** (`border-bottom` active), không nút xám nền.

| Tab | Badge |
| --- | --- |
| Bình luận | số event 24h; badge cam số nháp nếu `pending_drafts>0` |
| Messenger | tag nhỏ “Development” giữ |
| Khách hàng | `total_customers` |

Tab active class `active` như hiện tại; bind giữ nguyên.

### 7.1 Tab Bình luận

**Trên cùng — Nháp chờ duyệt** (nếu có): card như hiện tại (page tag, class, đề xuất, Gửi / Bỏ qua). Tiêu đề “Cần bạn duyệt (N)”.

**Thanh lọc:** “Mọi Fanpage” / “Mọi loại” — **bỏ** dấu `-- --`. Thêm chip lọc nhanh: Tất cả, Lead, FAQ, Spam.

**Danh sách comment = card**, không bảng 6 cột khi empty/ít hàng:

```
[FAQ]  14:32  ·  Trung tâm tin học Q7
Nguyễn A
“Cơ sở ở đâu vậy ạ?”
[SĐT 090****567]     [Tạo việc]
```

Bảng `.care-table` chỉ giữ khi `events.length > 8` (optional). Mặc định **luôn card** cho dễ đọc mobile — đơn giản hơn, chọn **luôn card**.

**Empty state** (0 event): không render `<table>` một dòng. Card giữa:

- Tiêu đề: “Chưa có bình luận”
- Nếu Care tắt: “Bật Care ở bước 2, rồi Quét ngay.”
- Nếu Care bật: “Bấm Quét ngay. Poller tự chạy mỗi 5 phút. Comment thử 3 câu: ở đâu / học phí / để SĐT.”
- Nút Quét ngay lặp lại ở đây.

### 7.2 Tab Messenger — **bỏ** “bản cập nhật tiếp theo”

Gọi `GET /fanpage-care/conversations` khi mở tab (đã có).

Mỗi thread (`page_id`, `psid`, `last_user_ts`, `last_page_ts`, `takeover_until`):

- Tên page từ `eligible_pages`
- PSID rút gọn `…` + 4 số cuối
- Cửa sổ 24h: còn / hết (so `last_user_ts`)
- Nếu `takeover_until > now`: chip “Nhân viên đang trả lời” + nút **Javis nhận lại** → `POST /fanpage-care/conversations/release-takeover` `{page_id, psid}`

Empty: “Chưa có tin Messenger. Cần Kết nối lại Facebook (quyền nhắn tin) và khách nhắn Page. Không HTTPS thì webhook không tới — comment vẫn vào tab Bình luận nhờ poll 5 phút.”

Banner Development **rút 2 dòng**, không chiếm nửa trang.

### 7.3 Tab Khách hàng

Giữ bảng + tìm + checkbox backup CRM. Empty: “Chưa có khách. Lead (có SĐT trên comment) sẽ hiện ở đây sau khi Quét.”

Nút Gộp: giữ prompt (không redesign modal trong PR này).

---

## 8. File và cache

| File | Việc |
| --- | --- |
| `server/fanpage_care.py` | `facebook_pages_status()` + `/state` thêm field |
| `tests/python/test_fanpage_care_state_perm.py` | 3 case trên |
| `dashboard/fanpage-care.js` | Viết lại `render`, `renderHeader`, empty, comments cards, messenger list. Giữ `api()`, `esc()`, draft send/reject, CRM modal. Poller: nếu `!_hostEl.isConnected` thì `stopAutoPoll`. |
| `dashboard/console.css` | Bổ sung class mới (checklist, stats, segment, cards, empty, tab underline). **Không xoá** class cũ nếu còn dùng. |
| `dashboard/index.html` | `console.css?v=68` → `?v=69`; `fanpage-care.js?v=1` → `?v=2` |

**Bắt buộc bump query string.** Không bump thì VPS giữ CSS cũ → lại ra “một cục”.

Không đụng `console.js` rail (đã có `fanpagecare`).

---

## 9. Class CSS mới (gợi ý, bám token hiện có)

```
.care-setup          hàng 3 bước
.care-setup-step     + .is-done / .is-todo
.care-stats          grid 4 thẻ
.care-stat           số + nhãn
.care-toolbar        toggle | segment | actions
.care-segment        3 nút
.care-segment button.active
.care-comment-list   cột card
.care-comment-card
.care-empty-hero     empty giữa trang
.care-thread-card    messenger
.care-tabs-nav       gạch chân; .care-tab-btn.active { border-bottom: 2px solid var(--accent); background: transparent; box-shadow: none; }
```

Mobile `< 720px`: stats 2×2, toolbar wrap, segment full width.

Light theme: chỉ dùng `var(--surface-1)`, `--text`, `--accent`, `--ok`, `--danger`, `--hairline`. Không hardcode nền đen.

---

## 10. Copy tiếng Việt (đúng chữ, đừng bịa)

- Toggle tắt: `Đang tắt Care`
- Toggle bật + suggest: `Đang bật — chỉ nháp`
- Bước 1 thiếu: `Facebook chưa Toàn quyền. Care chỉ ghi nhận, không trả lời được.`
- Quét skipped disabled: `Care đang tắt. Bật công tắc rồi quét lại.`
- Quét skipped no pages: `Chưa có Fanpage nào có brand kit trong brain.`
- Empty comments (Care bật): `Chưa thấy bình luận 24 giờ qua. Bấm Quét ngay, hoặc comment thử trên Page.`

Không dùng từ `Graph`, `perm`, `suggest` trên nhãn nút (mode value vẫn `suggest|auto|full`).

---

## 11. Kiểm thử

```
python -m pytest tests/python/test_fanpage_care_state_perm.py tests/python/test_fanpage_care_*.py tests/python/test_aux_complete_json.py tests/python/test_route_table.py
```

Thủ công (localhost hoặc VPS, **Ctrl+Shift+R**):

1. Care tắt + Facebook readonly/chưa full → thấy 3 bước, nút Mở Kết nối nhảy trang `mcp`.
2. Bật Care, mode Chỉ nháp, Quét ngay — empty hero, không bảng một dòng.
3. Tab Messenger không còn câu “bản cập nhật tiếp theo”.
4. Đổi theme sáng: chữ đọc được.
5. Hẹp cửa sổ ~400px: không tràn ngang, Kill không đè Quét.

---

## 12. Ngoài phạm vi

- Không bật `enabled` mặc định.
- Không tự nâng Facebook lên `full`.
- Không HTTPS/webhook.
- Không viết lại CRM merge thành modal đẹp (prompt cũ được).
- Không i18n `en.json` trừ khi sửa `vi` page.sub — có thể đổi sub thành: `Nháp bình luận, Messenger, danh sách khách — bật Care để bắt đầu.`

---

## 13. Definition of done

Người mở trang lần đầu **nhìn ra 3 việc phải làm**, không thấy “một cục” checkbox + bảng trống. Cache bust. Perm Facebook đúng. Messenger list API thật.
