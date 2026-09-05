---
type: wiki
updated: 2026-09-04
---
# Y chú khi đăng bài

Đọc file này TRƯỚC khi soạn caption và gen cover.

## Điều kiện được đăng

1. Page có file Brand Kit và dòng `Page ID:`.
2. Chủ đề bài khớp **thẻ khoá học** của kit (Default = `all`). Không khớp → không đăng page đó.
3. Ảnh lấy folder đúng thẻ trong `attachments/dataset/`.

## Nội dung (chuẩn chuyển đổi)

- Độ dài 60–120 dòng. Cấm tóm tắt 10–15 dòng
- Tiêu đề IN HOA + emoji ngành ở dòng 1
- 7 phần: tiêu đề, nỗi đau, giải pháp Sao Việt, cam kết vàng, module, ưu đãi, CTA + **chân trang đúng kit page** (địa chỉ / hotline / email / web). Không dán 12 cơ sở khi kit chỉ 1 chi nhánh.
- Đúng ngành theo thẻ. Cấm "thời đại 4.0", "bạn có biết", em dash
- Trước đăng: `python scratch/kit_chan_trang.py <Page ID>` rồi dán khối CHAN_TRANG. Plugin từ chối caption sai kit.
- **Ngoại lệ Royce Shop** (`Page test: true`, Page ID `988656934325292`): page thử nghiệm. Có kit là được đăng, không bắt đủ 12 địa chỉ + hotline + email. Fanpage Sao Việt thật vẫn chặn đủ chân trang.

## Ảnh & album (tỷ lệ 7/3 — bắt buộc)

- **Ảnh 1 = banner quảng cáo** thu hút: gen từ **1 raw dataset đúng thẻ khoá** + file Logo chính kit, **hoặc** gen AI full (vẫn dán logo kit). Lưu `_xuat/`.
- Album **7/3**: tối đa **3 ảnh gen**; **phần còn lại (~7) ảnh raw** `attachments/dataset/<thẻ>/`. Không album toàn AI.
- Cover VUÔNG 1:1 (2000×2000). Safe margin 15–18%. Cấm neon mạch, cấm vẽ chữ path file.
- **Logo / màu / font / giọng** = đúng kit page trên form Brand Kit + file `_quy-trinh-dang-bai.md`, `_the-khoa-hoc.md`.

## Lệnh ngắn

`Đồ họa Photoshop, đăng các page có thẻ do-hoa. Caption 7 phần. Cover 1:1 đúng ngành.`

`Kế toán ca tối, chỉ page thẻ ke-toan.`
