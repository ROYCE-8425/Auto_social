---
type: wiki
updated: 2026-09-04
---
# Vận hành nhiều Fanpage

Một hệ, nhiều page. **Không** một goal đăng hết trang nếu thẻ ngành không khớp.

## 4 lớp (đừng trộn)

| Lớp | Chỗ | Việc |
|---|---|---|
| Giọng chung | `_mac-dinh.md` | USP, cấm, CTA, pháp nhân |
| Thẻ ngành | `_the-khoa-hoc.md` + folder `attachments/dataset/<id>/` | 1 thẻ = 1 khoá / 1 kho ảnh |
| Từng page | kit page (tên = tên Fanpage) | Page ID Facebook, thẻ 1–nhiều, địa chỉ |
| Chạy việc | Chat / Việc | 1 goal = 1 chủ đề; chỉ page **có kit** và **có thẻ khớp** |

Default kit: `Thẻ khoá học: all` (full, kể cả thẻ mới).
Page chuyên đồ họa: chỉ thẻ `do-hoa` → bài kế toán **không** lên page đó.

## Hai cửa

- **Soạn bài Facebook** → nháp `sources/facebook-nhap/<slug>/YYYY-MM-DD.md`, không lên tường
- **Đăng Facebook** → lên tường, phải có `post_id`

## Loop hàng ngày (1 bài / 1 page)

File: `Javis/loops/dang-bai-hang-ngay.md`. Mặc định **TẮT**. Bật tay trên trang Việc định kỳ, mức **Toàn quyền**, và Facebook Trang phải đủ quyền đăng (không để chip 70 page ở Chỉ đọc).

## Chi phí API (cấu hình bạn chọn)

Giá Google Gemini API, tra 2026-09 (prompt ≤ 200K token). **Thinking của 2.5 Pro tính như output** ($10 / 1 triệu token).

| | Model | Đơn giá |
|---|---|---|
| Viết caption / việc nền | `gemini-2.5-pro` | $1.25 / 1 triệu input · $10 / 1 triệu output |
| 1 cover | `gemini-2.5-flash-image` (Nano Banana) | **~$0.039 / ảnh** (1024; ~1290 token ảnh × $30/1 triệu) |

1 bài gọn (3–5 lần gọi Pro + 1 ảnh, không 20 lần tool):

| | Token / lần (ước) | Tiền / bài |
|---|---|---|
| Pro input (skill + kit, không nhồi 56 file) | 8–25k × 3–5 lần | ~$0.04–0.12 |
| Pro output + thinking | 4–8k × 3–5 lần | ~$0.12–0.40 |
| 1 ảnh Flash Image | 1 cover | **$0.039** |
| **Tổng 1 bài** | | **~$0.20–0.55** (gọn ~$0.25; worker 10 vòng ~$0.80; 20 vòng như job Royce ~$1.50+) |

**55 Fanpage × 1 bài/ngày** (không Royce):

| | /ngày | /tháng 30 ngày |
|---|---|---|
| Ảnh | 55 × $0.039 = **$2.15** | **$64** |
| Text Pro (gọn ~$0.22) | **~$12** | **~$360** |
| **Tổng gọn** | **~$14** | **~$425** |
| Text Pro (thực tế worker 8–12 vòng ~$0.50) | **~$27.5** | **~$825** |
| **Tổng thực tế** | **~$30** | **~$890** |

Tier 1: cap billing **$250/tháng** + trần **$10 / 10 phút**.  
55 bài/ngày × $0.25 = $13.75/ngày → **~$413/tháng > $250**. Muốn đủ 55 page/ngày với 2.5 Pro thì gần như **phải lên Tier 2** (chi ≥ $100 + 3 ngày, cap $2.000) hoặc cắt còn ~20 bài/ngày (`$250/30/$0.40 ≈ 20`).

Giữ dưới $250: tối đa khoảng **18–22 bài/ngày** nếu Pro gọn; **8–12 bài/ngày** nếu job hay 10 vòng tool.

Hạn mức **Gemini API Tier 1** (công bố Google, tra 2026-09; số chính xác xem AI Studio → Rate limits):

| Chiều | Flash (text, việc nền) | Ảnh (Imagen / Nano Banana) | Ý với hàng đăng |
|---|---|---|---|
| RPM / IPM | ~150 yêu cầu/phút | ~10 ảnh/phút | 1 job không được bắn 20 lần tool |
| RPD | ~1.500/ngày | ~500 ảnh/ngày | 36 bài × 1 ảnh + vài lần chat vẫn dưới trần |
| TPM | ~1 triệu token/phút | — | Caption 60–120 dòng ổn nếu không nhồi 56 kit |
| Chi 10 phút | **$10** | chung 1 project | Retry 20 lần + Pro/Imagen 4 Ultra dễ 429 |
| Cap tháng | **$250** | — | ~36 bài/ngày * ~$0.05–0.15 ≈ $2–5/ngày |

Việc nền dùng **Flash**, không Pro. 1 vòng = 1 page, 1 cover gen.

| Chốt | Giá trị | Lý do |
|---|---|---|
| 1 vòng = 1 page | bắt buộc | Tránh đốt Gemini/Imagen và sập server |
| Chu kỳ | **25 phút** | Dưới 10 IPM; job xong mới tới job sau |
| Im lặng | 22-07 | 07:00–22:00 = 15 giờ → 36 khe |
| Trần | **36 vòng/ngày** | ~36/55 page/ngày, xoay ngày kia. Không nhồi 56+retry |
| Khoá học | ngẫu nhiên từ thẻ kit | Autocad chỉ ve-ky-thuat+tin-hoc _ai |
| Fail chân trang | bỏ tới mai (`khong-retry`) | Không vòng lặp đốt token |
| Fail mạng | thử lại 1 lần sau 2 giờ | Không rollback bài đã có post_id |

Chọn page: `skills/dang-bai-facebook/scripts/pick_next_fanpage.py` (in sẵn CHAN_TRANG). Job gọn **5 bước tool**, không đọc 56 kit. State: `Javis/dang-hang-ngay.json`.

## Luật 1 chủ đề → nhiều page (lọc thẻ)

Khi user bảo đăng tay “1 chủ đề cho các page có thẻ”:

1. Xác định **1 thẻ** từ brief (đồ họa / kế toán / vẽ kỹ thuật / tin học-AI…).
2. Lấy danh sách kit page có `Page ID` và thẻ chứa id đó (hoặc `all`).
3. Page không kit hoặc không thẻ → `POST_SKIP ly-do=khong-dung-the`. Không gọi Facebook.

Ảnh lấy đúng folder `attachments/dataset/<id-the>/`. Không lấy ngành khác cho có.

### Map chữ brief → thẻ (folder trên đĩa)

- Word, Excel, văn phòng, MOS, AI văn phòng → `tin-hoc _ai`
- AutoCAD, SolidWorks, cơ khí, vẽ kỹ thuật, nội thất CAD → `ve-ky-thuat`
- Kế toán, chứng từ, sổ sách, Misa → `ke-toan`
- Photoshop, Illustrator, đồ họa → `do-hoa`
- Thẻ mới: đúng `id` trong `_the-khoa-hoc.md`

Logo: `attachments/dataset/chung/` chỉ watermark.

## Ảnh

Kiểu A (có ảnh ngành): mẫu `_mau/mau-khoa-hoc-co-anh-goc.png`
Kiểu B (lịch lễ / không ảnh ngành): mẫu `_mau/mau-lich-le-tu-gen.png`
Lưu gen `_xuat/`. Cấm đăng file gốc dataset.

## Cấm

- Đăng page chưa có Brand Kit / chưa có Page ID
- Đăng sai thẻ (page đồ họa nhận bài kế toán)
- “Đăng hết page” cùng một brief khi thẻ không khớp
- Lấy Royce Shop (nếu còn) làm mẫu vận hành cả hệ — đó chỉ là page test nếu vẫn tồn tại
- Trộn 2 brief một bài; em dash; tự `fb_page_delete`

Muốn N page trong ngày: N goal lệch giờ, hoặc 1 chủ đề + hệ tự lọc theo thẻ.

## Nháp

`sources/facebook-nhap/<slug>/YYYY-MM-DD.md`
