# Plan: Tách thật Bình luận bài viết ≠ Hộp thư IB (không chỉ gắn tag)

| Trường | Giá trị |
|---|---|
| **Cho** | Gemini |
| **Ngày** | 2026-09-17 |
| **Bug** | Ảnh `/ops` Tổng quan: một list “Nháp chờ duyệt (16)” lẫn Quốc Khánh (Messenger) + Khách hàng (Facebook). Chip tag **không phải tách**. |

---

## 0. Vì sao bản hiện tại thất bại

API đã có `GET /fanpage-care/inbox?kind=comment|message` và `list_drafts(..., kind=)`.

`Inbox.tsx` **không gọi `kind`**. `loadData` lấy hết rồi lọc heuristic:

```ts
// SAI — cấm giữ
const isCommentDraft = (d) => {
  if (d.event_kind === 'comment') return true
  if (d.event_kind === 'message') return false
  return d.target_id.includes('_') || d.target_id.length <= 16
}
```

PSID Messenger và comment_id Graph **cùng dạng số**. Heuristic = đoán. Overview còn không lọc: `pendingDrafts` = mọi nháp.

**Quy tắc duy nhất:** `events.kind` (`comment` | `message` | `echo`). Draft theo `event_id` → `events.kind`. Không đoán `target_id`.

---

## 1. Hai không gian làm việc (không phải hai màu chip)

| | A. Bình luận trên bài | B. Hộp thư IB (Messenger) |
|---|---|---|
| Khách làm gì | Comment dưới post | Chat Business Suite / Messenger |
| `kind` | `comment` | `message` / `echo` |
| Gửi Graph | `fb_page_reply` | `fb_message_send` |
| UI | Hàng nháp: tên + nội dung comment + nháp Javis + Gửi / Bỏ | **Thread** theo người: lịch sử chat + ô trả lời + Gửi IB |
| Tab | `Bình luận bài viết` | `Tin nhắn IB` |
| Overview | Cột trái chỉ comment | Cột phải chỉ IB |

Chip Facebook/Messenger trên **cùng một hàng** = chưa tách. Xóa chip “Messenger” khỏi list comment.

---

## 2. API (đã gần đủ — bắt buộc dùng)

`GET /fanpage-care/inbox?kind=comment`  
`GET /fanpage-care/inbox?kind=message`

- `events` và `drafts` **cùng kind**. Draft không join được event → **loại khỏi comment** (không đoán).  
- `stats` theo cùng kind: `pending_comment_drafts`, `pending_message_drafts` (thêm field, đừng gộp 16).

Test: seed 1 comment draft + 1 message draft → `kind=comment` trả 1, `kind=message` trả 1. Cấm test heuristic.

---

## 3. `/ops` Hộp thư

`loadData` **hai request theo tab**, không một request rồi filter:

```ts
if (tab === 'comments') getInbox({ kind: 'comment', page_id })
if (tab === 'messenger') Promise.all([
  getInbox({ kind: 'message', page_id }),
  getConversations(page_id),
])
```

`useEffect` phụ thuộc `activeSubTab`.

Tab comments: **cấm** render `kind=message`. Badge = số nháp comment.

Tab messenger: **cấm** list nháp kiểu comment card. Một card / `psid`: last_body, nháp nếu có, [Mở chat] [Gửi nháp IB]. Nháp IB không hiện ở tab comment.

Xóa `isCommentDraft` / `target_id.includes('_')`.

---

## 4. `/ops` Tổng quan (ảnh đang hỏng)

Bỏ một khối “Nháp chờ duyệt (16)”.

Hai khối cạnh nhau (mobile xếp dọc):

1. **Bình luận chờ duyệt (N)** — chỉ `kind=comment`. Link → inbox tab comments.  
2. **Tin nhắn IB chờ (M)** — chỉ `kind=message`. Link → inbox tab messenger.

Hero: đừng “16 nháp” gộp. “3 comment · 13 IB” (số minh họa).

Thẻ stats: tách “Nháp comment” / “Nháp IB”. `pending_drafts` gộp chỉ để tương thích, UI không dùng làm tiêu đề chính.

---

## 5. Gửi nháp

Đã có nhánh `fb_message_send` vs `fb_page_reply` theo `event.kind`. Giữ. Test: draft message → không gọi `fb_page_reply`.

---

## 6. Copy

- Tab: `Bình luận bài viết` / `Tin nhắn IB`  
- Empty comment: `Chưa có comment trên bài.`  
- Empty IB: `Chưa có tin nhắn hộp thư. Bấm Kéo hộp thư IB.`  
- Cấm: “Sự kiện tương tác” lẫn comment+IB.

---

## 7. Definition of done (ảnh Tổng quan)

- Không còn một list 16 dòng lẫn Quốc Khánh (IB) và comment Facebook.  
- Tab comment: 0 tin “Jurassic World…” / “Hình ảnh đính kèm”.  
- Tab IB: có Quốc Khánh, Thằng Hề; không có Trần Như Ý (comment).  
- Pytest `kind=` tách. Không heuristic `target_id`.

Ctrl+Shift+R sau deploy. `mode=suggest` giữ.
