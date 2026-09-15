# Thiết kế: giãn header + nút đổi tông tối-đậm / tối-nhạt

Ngày: 2026-07-18
Trạng thái: đã brainstorm + duyệt hướng, chờ triển khai.

## Mục tiêu

Hai việc trên thanh header (`.hud-top`) của dashboard:

1. Header đang "díu dít": mọi thứ dồn về trái, ~414px bên phải bỏ trống. Giãn ra cho cân.
2. Thêm nút đổi tông giao diện ở góc phải header: lật giữa **tối-đậm** (hiện tại) và **tối-nhạt** (dim). KHÔNG có light mode nền trắng.

## Nguyên nhân header bị dồn

`.hud-top` là grid `1fr auto 1fr` với 4 con: `.brand`, `.navbar-brain`, `.hud-center-title`, `.hud-actions`.
Ở trang quản lý (`body.in-console`), `.brand` và `.hud-actions` bị `display:none` → auto-placement chỉ còn xếp `.navbar-brain` vào cột 1 và `.hud-center-title` vào cột 2, cột 3 (1fr, phải) trống hoác. Grid 4-con-3-cột cũng không bền ở màn home.

## Thiết kế

### Phần 1 - Header 3 nhóm rõ ràng

Gói các con hiện tại vào 3 nhóm cố định cột, thay cho 4 con phẳng:

```
<header class="hud-top">
  <div class="hud-top-left">   .brand + .navbar-brain (select brain + ➕🗑📁 + graph-stats) </div>
  <div class="hud-top-center"> .hud-center-title (JavisOS + ngày) </div>
  <div class="hud-top-right">  nút đổi theme (LUÔN hiện) + .hud-actions (ẩn khi in-console) </div>
</header>
```

- `.hud-top { grid-template-columns: 1fr auto 1fr; }` giữ nguyên; mỗi nhóm chiếm đúng 1 cột.
- `.hud-top-left { justify-self: start }`, `.hud-top-center { justify-self: center }`, `.hud-top-right { justify-self: end }`.
- Con bên trong nhóm ẩn (`.brand`, `.hud-actions`) chỉ tự co lại; nhóm vẫn giữ cột nên layout cân ở CẢ hai chế độ (home lẫn in-console).
- Nút đổi theme là con TRỰC TIẾP của `.hud-top-right` (ngoài `.hud-actions`) nên luôn hiện, kể cả khi in-console → lấp đúng cột phải đang trống.

### Phần 2 - Nút đổi theme + tông dim

- Nút icon "tương phản" (nửa tròn sáng/tối) trong `.hud-top-right`, style theo `.hud-icon-btn` sẵn có.
- Bấm → lật thuộc tính `data-theme` trên `<html>`: không có (mặc định) = tối-đậm; `data-theme="dim"` = tối-nhạt.
- Nhớ lựa chọn qua `localStorage["javis.theme"]`.
- Chống nháy: inline script NGAY đầu `<head>` đọc localStorage và đặt `data-theme` trước khi CSS vẽ.

Bảng màu dim (override `:root[data-theme="dim"]` trong style.css) - nhạt rõ hơn tối-đậm:

| Biến | Tối đậm (hiện tại) | Tối nhạt (dim) |
|------|--------------------|----------------|
| `--bg`     | `#0e0e16` | `#282a37` |
| `--bg2`    | `#181822` | `#343646` |
| `--bg3`    | `#22222e` | `#414353` |
| `--border` | `#36364c` | `#545872` |
| `--text`   | `#f3f3fb` | `#eef0f7` |
| `--text2`  | `#c0c0da` | `#c2c5d6` |
| `--text3`  | `#9a9ab6` | `#9498ad` |

`--accent`, `--accent2`, `--green`, `--red`, `--yellow`, `--font` giữ nguyên (accent hợp cả hai tông).

## Phạm vi & ranh giới

- Đổi tông chỉ tác động các bề mặt DÙNG biến CSS (header, rail, cview, các trang, chat, panel). Graph 3D / starfield ở cockpit dùng màu hard-code → GIỮ nền tối như cũ. Chấp nhận được vì cả hai tông đều tối, nhìn liền không chỏi. Không đụng graph3d.js/starfield trong phạm vi này.
- Rail (console.css) đã dùng biến riêng (`--rail-bg`, `--glass-brd`) + vài rgba hard-code; phần lớn theo `--text*` nên đổi tông tự ăn. Chấp nhận vài chỗ hard-code không đổi (tinh chỉnh sau nếu cần).
- Mobile: header cùng CSS; nhóm 3 cột vẫn chạy. Nút theme vẫn hiện góc phải.

## File đụng tới

- `dashboard/index.html`: gói header thành 3 nhóm; thêm nút theme; thêm inline script chống nháy đầu `<head>`.
- `dashboard/style.css`: layout 3 nhóm header; `:root[data-theme="dim"]` bảng màu dim; style nút (dùng lại `.hud-icon-btn`); bump `?v`.
- Xử lý bấm nút + lưu localStorage: script nhỏ (inline cuối body hoặc app.js), gắn 1 lần.

## Kiểm thử

- Home + in-console: header cân, nút theme luôn ở góc phải, không dồn cục.
- Bấm nút: `<html>` đổi `data-theme`, nền/panel đổi tông ngay, icon phản hồi, localStorage lưu.
- Tải lại trang: giữ đúng tông đã chọn, không nháy tối-đậm rồi mới đổi.
- Graph cockpit vẫn nền tối ở cả hai tông (không kỳ vọng đổi).
