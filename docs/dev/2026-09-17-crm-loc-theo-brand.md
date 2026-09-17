# PROMPT GEMINI — CRM: Javis lọc và đưa khách vào đúng brand (ảnh trống)

Ảnh: `/ops#customers`, phạm vi **Nhóm Game BSN**, bảng **rỗng**, tiêu đề cứng **“Khách Hàng (Sao Việt CRM)”**. Sai luồng: đang BSN mà CRM nói Sao Việt; không thấy khách dù hộp thư đã có comment/IB BSN.

Cấm: CRM mới, Firebase, chỉ hiện lead có SĐT.

---

## BẮT ĐẦU

### 0. Bệnh

`Customers.tsx` không đọc `CareScope`. `GET /fanpage-care/customers` **không** nhận `brand` / `page_id`. `search_customers` LIKE trên name/phones, **không** lọc page. Tiêu đề hardcode Sao Việt.

Ingest đã gọi `get_or_create_customer` trong `process_inbound_comment` / `_message` — nhưng:

- `tag` chỉ gắn khi `class==lead` → FAQ/ambiguous **không có tag brand**
- Không lưu `brand` (`bsn`|`saoviet`)
- Không backfill từ `events` đã có
- UI empty nuốt lỗi API (`catch console.error`)

Hệ quả: chọn BSN → tưởng CRM Sao Việt trống.

### 1. Luật đưa khách vào dự án (Javis lọc)

Mỗi comment/IB **đã ingest** → 1 hồ sơ CRM (không chỉ lúc có SĐT).

| Tín hiệu | Ghi |
|---|---|
| `page_id` | Kit → `brand` (`game-gia-re-bsn` → `bsn`, còn lại `saoviet`) + `campus` = tên kit |
| `from_id` | identity `fb_comment_from` + page |
| `psid` | identity `fb_psid` + page |
| SĐT regex VN | identity `phone` **global** (gộp xuyên page **cùng brand**; **không** gộp BSN với Sao Việt) |
| `class` | tags: `faq`/`lead`/`…` + luôn tag `bsn` hoặc `saoviet` |
| `kind` | `comment` / `message` trên timeline |

Gộp: cùng SĐT + cùng brand → 1 crm_id. Cùng người comment + IB cùng page → 1 hồ sơ. **Cấm** gộp khách BSN với học viên Sao Việt dù trùng SĐT (thêm `brand` vào identity phone: `page_id` để `''` nhưng `kind=phone_bsn` / `phone_saoviet` hoặc cột `brand` trên customers).

**Cột mới** `customers.brand TEXT` (default `''`). Migration ALTER. Index `(brand, updated_ts)`.

### 2. API list theo phạm vi

`GET /fanpage-care/customers?q=&brand=&page_id=&limit=`

- `page_id` → `page_ids` JSON chứa id
- `brand=bsn|saoviet` → `customers.brand` hoặc page_id ∈ kit brand
- Không query → tất cả (owner); `/ops` **luôn** gửi brand/page theo thanh phạm vi

`search_customers(..., brand=, page_ids=)`

Empty: `{ customers: [], reason: "none_in_scope" }` — UI không coi là lỗi.

### 3. Backfill (một lần, nút chủ máy)

`POST /fanpage-care/customers/backfill` (owner/manager):

- Duyệt `events` 90 ngày, `from_id`/`thread_id` + `page_id` → `get_or_create_customer` + `brand` từ kit.
- Idempotent. Trả `{ created, updated }`.

Không có nút thì CRM mãi trống dù 144 comment.

### 4. UI `/ops` Khách hàng

- Title: `Khách hàng · {scopeLabel}` (BSN / Sao Việt / Tất cả / tên page). **Cấm** “Sao Việt CRM” khi chip BSN.
- `useCareScope()`: `loadCustomers` khi đổi scope/search.
- `getCustomers({ q, brand, page_id })`.
- Cột: Tên, SĐT (che), Nguồn (Comment/IB), Brand chip, Campus/shop, Tag, Cập nhật.
- Empty BSN: *“Chưa có hồ sơ Game BSN. Kéo comment/IB trên Hộp thư rồi bấm Đồng bộ từ tương tác (chủ máy).”*
- Nút **Đồng bộ từ tương tác** → backfill (manager+owner).
- Click dòng → drawer: behavior + timeline (đã có).

Staff: xem, không xóa/merge (RBAC hiện có).

### 5. Test

- Ingest comment page `343562028848465` → customer `brand=bsn`, hiện `?brand=bsn`, **không** hiện `?brand=saoviet`.
- Hai event cùng `from_id` → 1 crm.
- SĐT cùng số, một BSN một Sao Việt → **2** hồ sơ.
- Backfill 3 events không customer → `created>=1`.
- UI: không hardcode “Sao Việt CRM”.

### 6. Cấm

- Chỉ lưu lead có SĐT (mất FAQ/IB).
- CRM riêng từng kênh rồi không gộp comment+IB cùng page.
- Fake 16 khách trên UI.

Definition of done: chọn **Nhóm Game BSN** → list có Trần Như Ý / Ẩn danh / khách IB (sau backfill hoặc ingest mới). Tiêu đề **Game Giá Rẻ BSN**. Nhóm Sao Việt không thấy khách BSN.

## HẾT
