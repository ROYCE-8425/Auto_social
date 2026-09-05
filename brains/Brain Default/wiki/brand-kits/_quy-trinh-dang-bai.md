---
type: wiki
updated: 2026-09-05
---
# Quy trình đăng bài (1 page = 1 kit = 1 bài)

Luồng chuẩn cho Kanban, workflow `dang-bai-that-facebook`, và loop `dang-bai-hang-ngay`.
Mọi caption + cover **bắt buộc** lấy từ **đúng 1 file** `wiki/brand-kits/<kit-page>.md` (form Brand Kit Fanpage). Cấm copy kit page khác. Cấm bịa logo/màu/địa chỉ.

## Sơ đồ 1 vòng

0. **Tài liệu hệ thống** — `_y-chu-dang-bai.md`, `_quy-trinh-dang-bai.md`, `_the-khoa-hoc.md`.
1. **Chọn page** — `pick_next_fanpage.py` hoặc brief. In `NEXT=1` + `KIT_VISUAL` + `CHAN_TRANG` + `luat_anh=7/3`.
2. **Đọc đúng 1 kit page** — không đọc 56 kit, không `fb_pages_list`.
3. **Caption** — 7 phần, 60–120 dòng, giọng kit, CHAN_TRANG xuống dòng, không Markdown.
4. **Ảnh 1 = banner** — gen từ raw+logo hoặc AI full+logo. `_xuat/`.
5. **Album 7/3** — tối đa 3 gen; còn lại raw. `pick_photos`.
6. **Đăng 1 lần** — `fb_page_album` / `fb_page_photo`. CẤM `fb_page_post`.
7. **Ghi nhận** — `--ok` / `--fail`. 1 page tối đa 1 bài OK / ngày.

## Plugin chặn (không vòng lại)

| ly-do | Khi nào |
|---|---|
| `chua-co-brand-kit` | Page không có file kit / Page ID |
| `caption-ngan` | < 45 dòng không rỗng |
| `dia-chi-mot-dong` | Một dòng có ≥2 dấu `\|` |
| `chan-trang-sai-kit` | Thiếu hẳn hotline hoặc không 1 mẩu địa chỉ kit (page thật) |
| `anh-goc-chua-gen` | Ảnh 1 không nằm `_xuat/` |
| `gen-thua` | Hơn 3 file `_xuat` (không kể crop `album_ready`) |
| `caption-ngan` / text-only | `fb_page_post` khi đã có kit |

## Hàng ngày (chưa bật loop)

Loop `Javis/loops/dang-bai-hang-ngay.md`: 07–22, 18 phút/vòng, max 48, 1 page/vòng, Royce loại trừ. `enabled: false` cho đến khi chủ bật. Mục tiêu: mỗi Fanpage có kit = 1 bài/ngày, thẻ ngẫu nhiên trong thẻ đã tick trên Brand Kit.
