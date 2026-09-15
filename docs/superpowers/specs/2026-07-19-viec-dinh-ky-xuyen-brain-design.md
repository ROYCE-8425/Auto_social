# Việc định kỳ xuyên brain: gộp hiển thị, di chuyển, nhớ brain Telegram

Ngày: 2026-07-19
Trạng thái: đã duyệt thiết kế, triển khai luôn theo yêu cầu chủ dự án

## Vấn đề (gốc, không phải cảm giác)

Chủ dự án: "Việc định kỳ tạo qua Telegram mặc định lưu vào default brain, lúc tìm trong
brain đang làm việc thì không có. Dùng thực tế thấy rối."

Điều tra tại file:line xác nhận đang có HAI khái niệm "brain hiện tại" tách rời:

- **Telegram** (`main.py:4627` `_tg_brain`): mỗi chat gắn brain riêng trong `_TG_SESS` (RAM).
  Chưa gõ `/brain` thì rơi về brain mặc định (`_read_loop_config().get("brain","brain")`).
  Thực tế gần như không ai gõ `/brain`, nên mọi việc tạo qua Telegram âm thầm vào Brain Default.
- **Dashboard** (`console.js:919,950`): trang Việc định kỳ (`renderSelfImprove`) CHỈ đọc đúng
  brain đang chọn ở sidebar (`fbrain()` = `currentBrainPath()`). Loop, nhắc hẹn, nút
  bật/tắt/xoá đều gắn `brain=fbrain()`.

Hai cái không dính nhau. Tạo việc qua chat (vào Brain Default) rồi mở dashboard đang ở brain
khác thì trang Việc trống. **Việc VẪN chạy** (scheduler quét mọi brain đã đăng ký,
`self_improve.py:423` `scheduler_brains`), nên đây thuần là vấn đề NHÌN THẤY và ĐIỀU KHIỂN,
không phải mất việc.

Thêm một tầng nữa: `_TG_SESS` bị `_TG_SESS.clear()` xoá mỗi lần bot khởi động lại
(`main.py:5098`). Nên kể cả đã `/brain` sang brain khác, restart một phát là về mặc định.

## Không gộp thành một kho (đã cân nhắc và loại)

Lưu tách theo brain là CỐ Ý: loop là file `.md` trong `<vault>/Javis/loops/` (sửa trong
Obsidian, commit theo git brain, `self_improve.py:11`); nhắc hẹn là `<vault>/Javis/reminders.json`.
Spec 2026-07-17 đã chốt giữ vậy. Hướng đúng không phải nhét chung một kho, mà là làm **lớp
hiển thị và lớp điều khiển xuyên brain**, còn lớp lưu giữ nguyên.

## Thiết kế: 5 mảnh

### Mảnh 1 - Hiển thị gộp mọi brain

Endpoint mới `GET /viec/all` (main.py, nơi có sẵn cả `loop_feature`, `reminders` feature và
`list_brains`). Lặp qua `list_brains()` (KHÔNG chỉ brain đã đăng ký - phải thấy cả brain có
loop/nhắc mà chưa từng mở), mỗi brain trả:

```json
{"brains": [
  {"name": "Kim Khí Hà Lộc", "path": "...", "is_default": false,
   "loops": [ <loop_view + brain gắn kèm> ],
   "reminders": [ <pending reminder + brain gắn kèm> ]}
], "running": false, "running_slug": ""}
```

- loop item tái dùng `loop_feature.loop_view(brain, lp, state)` y trang hiện tại, thêm
  `brain_name` + `brain_path`.
- reminder item tái dùng view `pending` của `reminders._load` + `_view`, thêm `brain_name` +
  `brain_path`.

`renderSelfImprove` (console.js) đổi từ đọc `/loops?brain=` + `/reminders?brain=` (một brain)
sang đọc `/viec/all` (mọi brain). Nhóm theo brain: brain đang chọn ở sidebar (`fbrain()`) lên
đầu, làm nổi; các brain khác gom dưới, mỗi nhóm có tiêu đề tên brain. Mỗi thẻ loop/nhắc gắn
nhãn brain của nó. Nút bật/tắt/xoá/chạy-ngay/huỷ đổi từ gửi `fbrain()` sang gửi **brain của
chính item** (`lp.brain_path` / `r.brain_path`) - đây là điểm dễ sai nhất: hiện tất cả nút
gửi `fbrain()`, gộp rồi mà quên đổi thì thao tác lên item brain khác sẽ nhắm nhầm brain.

### Mảnh 2 - Di chuyển việc sang brain khác

Nút "Chuyển sang brain..." trên mỗi thẻ, đổ danh sách brain (trừ brain hiện tại của item).

- **Loop**: `POST /loops/move` (self_improve router): `slug`, `from_brain`, `to_brain`.
  - Đọc loop nguồn (`get_loop`); không có → lỗi.
  - Đích đã có file cùng slug (`_loop_path(to_brain, slug).exists()`) → **lỗi, KHÔNG ghi đè**
    (định danh theo tên file, `self_improve.py:319`; builtin `tu-cai-tien-javis` có ở mọi brain
    nên đây là va chạm thật sẽ gặp).
  - Đang chạy đúng loop đó (`self._running`) → lỗi "đang chạy, thử lại sau".
  - `save_loop(to_brain, lp)` → `delete_loop(from_brain, slug)` → dời entry
    `loop-state.json` (nguồn sang đích; không dời được thì để đích chạy mới) →
    `register_brain(to_brain)`.
- **Nhắc hẹn**: `POST /reminders/move` (reminders router): `id`, `from_brain`, `to_brain`.
  - Pop record khỏi `<from>/reminders.json`, push vào `<to>/reminders.json`, giữ nguyên `id`
    và mọi field (chat_id, cron, due_at...). Lưu cả hai file.

`owner_chat`/`chat_id` giữ nguyên khi chuyển → vẫn báo về đúng người đã đặt.

### Mảnh 3 - Tạo trên dashboard chọn brain đích

Form "+ Loop mới" (console.js `openForm`) thêm ô chọn brain đích (dropdown đổ từ
`/brains`), mặc định brain đang xem (`fbrain()`). `#lpSave` gửi `brain` = giá trị chọn thay
vì cứng `fbrain()` (`console.js:847`). Không đổi backend `POST /loops` (đã nhận `brain`).

### Mảnh 4 - Chat báo rõ brain khi tạo việc

`javis_schedule` (system/plugins/javis-schedule/plugin.py) hiện báo "Đã tạo... tại
Javis/loops/<slug>.md" nhưng KHÔNG nói brain (`plugin.py:249`). Sửa để câu xác nhận nêu tên
brain: "Đã tạo việc 'Quét đơn' trong brain **Kim Khí Hà Lộc**, chạy mỗi 120 phút, đang tắt,
vào tab Việc để bật."

- `brain_name = Path(vault_root).name` (vault_root là path brain phiên).
- Sửa `_create_loop_file` (thêm brain_name vào câu trả về) và `_post_reminder` (nhận brain_name,
  thêm vào câu "Đã đặt... trong brain X").

Đây là chỗ bịt cái rối NGAY lúc tạo: user biết việc rơi vào brain nào tức thì, không phải đi
tìm mới ngã ngửa.

### Mảnh 5 - Nhớ bền lựa chọn /brain của Telegram

Vấn đề: brain phiên nằm trong `_TG_SESS` (RAM), mất khi restart.

- Map bền `chat_id -> tên brain`, ghi `STATE_DIR/tg_brain.json` (server state, gitignored,
  xuyên brain, KHÔNG nằm trong vault nào - đúng chỗ như `.sessions.json`, `config.py:228`).
- Lưu theo **tên brain**, không phải path tuyệt đối (bền qua Docker/local + brain đổi chỗ).
  Đọc mới resolve tên -> path (`Path(BRAINS_DIR)/name`); brain đã xoá -> về mặc định + dọn
  entry cũ.
- `_tg_set_brain(chat_id, path)`: ghi cả phiên sống (như cũ) lẫn map bền (`name=Path(path).name`).
- `_tg_brain(chat_id)`: phiên sống trước -> map bền -> mặc định.
- `_TG_SESS.clear()` lúc restart giữ nguyên (vẫn reset hội thoại); brain sống sót vì đọc từ
  map bền tách biệt.

Kết quả: `/brain` sang brain nào thì dính đó tới khi đổi cái khác, kể cả sau restart.

## Ngoài phạm vi

- Cách Telegram chọn brain mặc định khi CHƯA từng `/brain` (vẫn về brain mặc định Settings) -
  giữ nguyên. Mảnh 4 + 5 làm nó minh bạch và bền là đủ; không thêm khái niệm "brain làm việc
  chính" (chủ dự án không muốn thêm cấu hình).
- Kanban tasks (`tasks.py`) - không có đồng hồ, không thuộc trục việc-định-kỳ. Giữ nguyên.
- Gộp một kho lưu - đã loại ở trên.

## Rủi ro

1. **Nút thao tác nhắm nhầm brain sau khi gộp.** Điểm dễ sai nhất: mọi nút hiện gửi `fbrain()`.
   Gộp xong PHẢI đổi sang brain của chính item. Cần test: bật/xoá item ở brain B khi sidebar
   đang brain A phải tác động brain B.
2. **Di chuyển loop trùng slug ở đích** (builtin `tu-cai-tien-javis` có ở mọi brain) - phải
   fail rõ, KHÔNG ghi đè. Cần test va chạm.
3. **Map bền lưu tên brain** - brain xoá/đổi tên giữa chừng phải fail-safe về mặc định, không
   crash `_tg_brain`.
4. **`/viec/all` quét mọi brain mỗi lần load** - với nhiều brain có thể chậm. Chấp nhận được ở
   quy mô ~4 brain; nếu phình thì thêm cache sau (ngoài phạm vi).

## Kiểm thử (tối thiểu)

- `test` di chuyển loop: thành công (file dời + register), va chạm slug (từ chối), loop đang
  chạy (từ chối).
- `test` di chuyển nhắc hẹn: record sang đúng file đích, giữ id.
- `test` nhớ bền tg brain: set -> đọc lại sau khi "restart" (dựng lại state từ file) trả đúng
  brain; brain xoá -> về mặc định.
- `test` javis_schedule: câu trả về create có tên brain.
- `test` `/viec/all`: gắn đúng brain_name/brain_path cho từng item (nếu dựng được app trong test).
