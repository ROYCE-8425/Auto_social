# Spec: UX trang Kết nối triệt để (khối A, B, D)

> Duyệt qua chat 2026-07-27. Bối cảnh: vụ nghi oan Google Workspace (0.9.189) lộ ra
> chuỗi bệnh của trang Kết nối: không thấy sức khoẻ, kết nối lại khó, 4 đường Google
> rối, guide tường chữ. Khối C (banner não mất đăng nhập) để đợt sau.

## Khối A - Sức khoẻ thường trực + kết nối lại một chạm (0.9.192)

### Server
- Module mới `server/connect_health.py`:
  - Vòng nền check mỗi `HEALTH_INTERVAL` (10 phút): với từng connection enabled,
    ping `pool.list_tools(spec)` (rẻ, không gọi tool thật), timeout ngắn.
  - Trạng thái in-memory: `{conn_id: {ok, kind, message, checked_at}}`. Không persist,
    sau restart quét lại sớm (delay ngắn sau startup).
  - Phân loại lỗi sang tiếng người tại server (`classify_error`):
    - 401 / invalid_grant / "OAuth session expired" → kind `auth`, "Hết phiên đăng nhập"
    - timeout / connect error → kind `net`, "Dịch vụ không phản hồi"
    - lỗi spawn stdio (FileNotFoundError, exit sớm) → kind `spawn`, "Không khởi động được trình kết nối trên máy"
    - còn lại → kind `unknown`, cắt ngắn thông điệp gốc.
- Endpoint:
  - `GET /connect/health` → map trạng thái mọi connection.
  - `POST /connect/health/check` (id) → ép check ngay một connection, trả kết quả.
- Test: `test_connect_health.py` - classify đủ nhánh, vòng check với pool giả,
  endpoint shape, ép check.

### UI (console.js)
- Chip tài khoản gắn chấm màu: xanh (ok), vàng (chưa check / đang check), đỏ (lỗi).
  Tooltip: thông điệp + thời điểm check.
- Card có connection lỗi kind `auth` → nút "Kết nối lại":
  - oauth → gọi `/connect/oauth/start` với conn id sẵn có (giữ id, label, quyền).
  - apikey → mở modal dán key mới, submit đè secrets qua `/connect/update` (mở rộng
    nhận secrets mới nếu chưa có).
- Poll `/connect/health` khi mở trang + mỗi 60s khi đang ở trang.

## Khối B - Gộp Google một cửa + wizard (0.9.193)

- Catalog: 5 connector Google thêm `group: "google"`. UI thấy group → gom về MỘT
  card "Google" trong Kho. Bấm card → màn chọn dịch vụ (Lịch, Gmail, Tasks,
  Drive/Docs, Keep): mỗi dòng 1 câu quyền tới đâu + badge độ khó. Map dịch vụ →
  connector là việc của UI, user không thấy tên kỹ thuật.
- `auth.steps` (mảng có cấu trúc) thay guide tường chữ: mỗi bước
  `{text, link?, link_label?, copy?}`. UI render stepper; giữ `guide` cũ làm
  fallback cho connector chưa chuyển.
- Ô nhập key nhận kéo thả file JSON client của Google (bóc client_id/client_secret
  từ cả `web` lẫn `installed`).
- Dùng lại key: nếu connection Google khác đã có client_id/secret → nút
  "Dùng lại key của <tên>", server copy secrets (endpoint mới hoặc mở rộng
  /connect/add nhận `reuse_from: conn_id` - KHÔNG trả secrets về browser).
- Test: schema steps trong catalog, reuse_from không lộ secrets, map nhóm.

## Khối D - Đánh bóng (0.9.194)

- Hai khu ambient (Claude Code, Codex) gập mặc định.
- Chữ "MCP" rời mọi text chính, chỉ còn trong "Tự thêm (nâng cao)" + chi tiết.
- Card kho: badge cách đăng nhập tiếng người ("Dán key" / "Đăng nhập Google" /
  "Quét QR" / "Bấm là xong").
- Mobile: grid 1 cột, chip không tràn. Bổ sung icon còn thiếu logo.

## Nguyên tắc chung
- Không đổi schema backend connection; mọi thứ tương thích ngược.
- UI string tiếng Việt có dấu, không em dash.
- Mỗi khối ship một bản riêng, test pass rồi mới sang khối sau.
