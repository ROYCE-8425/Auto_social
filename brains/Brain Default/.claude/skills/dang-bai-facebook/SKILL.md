---
name: Đăng bài Facebook
description: "Co anh dataset: album tat ca goc (cam 1 anh, cam gen). Khong anh lien quan: moi gen 1 tam."
group: Marketing
---

# Đăng bài Facebook

Doc `wiki/brand-kits/_y-chu-dang-bai.md` truoc. Engine viec nen tu gen anh bang tool CUA ENGINE. Khong bat ChatGPT. Khong dung Gemini CLI (da go).

- **Grok Build:** `image_edit` (kieu A, khoa anh dataset) / `image_gen` (kieu B).
- **Antigravity CLI (`agy`, goi Google):** model Gemini trong Antigravity. Sinh anh bang tool anh native cua `agy` (GenerateImage / Nano Banana neu model co). Luu file vao `attachments/dataset/_xuat/`. Cung prompt `references/prompt-poster.md` + mau `_mau` de so chat luong voi Grok.
- **Gemini API key:** khong co image_edit nhu Grok CLI. De so anh Gemini vs Grok thi dung Antigravity CLI, khong dan API.

## 1. Chọn folder dataset theo brief (Luật A)

| Chữ trong brief | Folder |
|---|---|
| Word, Excel, văn phòng, MOS | `attachments/dataset/tin-hoc/` |
| AutoCAD, SolidWorks, CNC, cơ khí | `attachments/dataset/co-khi/` |
| Kế toán, chứng từ, sổ sách | `attachments/dataset/ke-toan/` |
| Photoshop, Illustrator, đồ họa | `attachments/dataset/do-hoa/` |
| Ads, Facebook Ads, SEO, Marketing | `attachments/dataset/marketing/` |
| AI, ChatGPT, Copilot | `attachments/dataset/ai/` |
| Trẻ em, Scratch, lập trình | `attachments/dataset/tre-em/` |
| Tiếng Hàn | `attachments/dataset/tieng-han/` |
| Logo only | `attachments/dataset/chung/` (chỉ làm watermark, không làm ảnh bài) |

Kit page có **nhiều ngành**: dòng `Folder anh (dataset): tin-hoc, ke-toan, co-khi`. Brief chọn 1 ngành trong list đó. Không khóa 1 folder/page.

Đếm file jpg/png/webp trong folder ngành (không tính `chung`, `_mau`, `_xuat`). Đó là ảnh liên quan.

Sau post_id: chi append path **anh goc dataset** vao `_anh-da-dung.md` (khong ghi file `_xuat`). Uu tien goc chua dung; het goc moi thi dung lai goc (khong rut xuong 1 tam).

**Anh gen AI khong tai su dung:** CAM lay bat ky file trong `_xuat/` cua vong truoc lam cover/album. Cover phai gen MOI trong vong nay (neu can). Co post_id: **xoa** file cover vua gen trong `_xuat/` (Facebook da co ban). Giu nguyen anh raw trong `tin-hoc/`, `ke-toan/`, ...

## 2. Khi nào gen, khi nào dùng ảnh có sẵn (Luật B)

Liệt kê file ảnh trong folder ngành. Gọi N = số file. Đọc `_mau/bo-cuc.md` (GIỮ / BỎ).

**Cover (ảnh đầu) xoay 2 kiểu cốt lõi (ĐÃ XOÁ STYLE 3 NEON)** (đọc `_mau/bo-cuc.md`). Cấm lặp 2 bài liên tiếp cùng kiểu. CẤM mở `_xuat` cũ.

- **Kiểu 1 Poster mockup studio 1:1 (chuẩn như `mau-poster-do-hoa.png`):** Thiết kế tỷ lệ VUÔNG 1:1 (2000x2000 hoặc 1200x1200 px). Hình ảnh học viên/chuyên gia trẻ trung ngồi bên laptop + icon 3D phần mềm bay nổi khối (Word, Excel, AutoCAD, Misa, Ps...) + tiêu đề to rõ nền xanh nhận diện Sao Việt + badge ưu đãi vàng "ƯU ĐÃI 30% HỌC PHÍ - KÈM 1-1" + footer hotline. Chữ không đè nhau, safe margin 15-18%.
- **Kiểu 2 Ảnh gốc 1:1 + Khung thương hiệu:** Kết hợp ảnh lớp học thật từ dataset + khung chữ thanh dưới sắc nét (mẫu A-full 1:1), logo Sao Việt, không che mặt học viên.
*(Style 3 Neon viền mạch điện tối tăm đã xoá bỏ hoàn toàn khỏi hệ thống).*

Xoay luân phiên 2 kiểu cover trên. Cấm 2 bài liên tiếp cùng kiểu.

- **Bố cục đa dạng chuẩn Facebook 2026 (4, 6, 7, 8 ảnh)**:
  - **Ảnh 1 (Cover / Hero Banner)**: **BẮT BUỘC HÌNH VUÔNG 1:1** (2000x2000 hoặc 1200x1200 px). Nằm trọn 100% trong ô vuông góc trên bên trái, KHÔNG BAO GIỜ BỊ CẮT XÉN 2 bên mép.
  - **Số lượng ảnh bài đăng**: Linh hoạt **4, 6, 7, hoặc 8 ảnh** (tự động chọn và chuẩn hóa qua lệnh `pick_photos`):
    - **Bố cục nhiều hơn 5 ảnh (6, 7, 8 ảnh...) - Chuẩn vàng Facebook 2 cột**:
      - `photos[0]` (Ảnh chính 1): Banner Cover VUÔNG 1:1 (2000x2000).
      - `photos[1]` (Ảnh chính 2): Ảnh lớp học đẹp nhất crop VUÔNG 1:1 (2000x2000).
      - `photos[2..N]` (Ảnh phụ): Ảnh lớp học crop NGANG 3:2 (2000x1330). Ô thứ 5 hiển thị huy hiệu `+N` (`+1`, `+2`, `+3`...).
      - Hai cột cân bằng tuyệt đối: Cột trái (2 x 2000 = 4000) = Cột phải (3 x 1330 = 3990 ≈ 4000).
    - **Bố cục 4 ảnh**: Cả 4 ảnh đều VUÔNG 1:1 (2000x2000) -> Facebook hiển thị lưới 2x2 gồm 4 ô vuông bằng nhau hoàn hảo.
  - **Cơ chế Chuẩn hóa & Random tự động**:
    - Chạy lệnh:
      `python "brains/Brain Default/scratch/hub_call.py" pick_photos <folder> <cover_path> random`
    - Lệnh này sẽ tự động chọn số lượng ảnh (4, 6, 7 hoặc 8), tự động chuẩn hóa Ảnh 1 và Ảnh 2 thành VUÔNG 1:1 (2000x2000), các ảnh phụ thành NGANG 3:2 (2000x1330), lưu vào thư mục `_xuat/album_ready/` và trả về danh sách ảnh chuẩn khít Facebook.

Cấm Bach Khoa / Truong Thinh / Zoom. Prompt: `references/prompt-poster.md`.

## 3. Cách gọi album chuẩn Facebook (Luật C)

Lọc trùng TRƯỚC khi đăng:
- Bỏ file tên ` (1)` / `copy`.
- Bỏ file trùng hash (cùng byte).
- File dùng làm Ảnh 1 của `image_edit` (cảnh trên cover) **không** nằm trong photos[1..]. Cover đã hiện cảnh đó.
- Sau lọc, nếu chỉ còn 1 cảnh duy nhất: `fb_page_photo` cover **hoặc** gốc, **cấm** album cover + đúng gốc đó.

Số lượng ảnh gửi vào `fb_page_album`:
- Tự động lấy danh sách ảnh ngẫu nhiên qua lệnh:
  `python "brains/Brain Default/scratch/hub_call.py" pick_photos <folder> <cover_path> random`
- Trả về danh sách `photos` chuẩn gồm 4, 6, 7 hoặc 8 ảnh (cover luôn là photos[0]).
- Cover không split-navy nếu lần trước đã split.

## 4. Khớp chữ trên ảnh và caption trước khi đăng (Luật D)

Trước khi bấm đăng: bắt buộc đối chiếu ngày tháng, giờ giấc, số liệu trong caption với chữ trên ảnh.
Nếu lệch (ví dụ ảnh ghi nghỉ 25/09 mở lại 26/09 mà caption ghi mở lại 28/09): PHẢI sửa caption cho khớp 100% với ảnh, tuyệt đối không đăng bài khi số liệu lệch nhau.

## 5. Đăng đúng 1 lần, cấm tự xóa bài (Luật E)

N>=2: chỉ `fb_page_album` 1 lần. N<=1: `fb_page_photo` 1 lần. Không thử cả relative và absolute.
CẤM gọi `fb_page_delete` trừ khi người dùng ra lệnh rõ ràng kèm đúng post_id cần xóa. Tuyệt đối không tự đăng thử rồi tự xóa.

## 6. Goal ngắn, tự bung (Luật F)

**CẤM đăng page chưa có Brand Kit.** Trước khi gọi `fb_page_*`: đọc `wiki/brand-kits/*.md`, chỉ đăng page có file kit và dòng `Page ID:` khớp. Không có kit → `POST_SKIP ly-do=chua-co-brand-kit`.

**CẤM đăng sai thẻ.** Đọc `_the-khoa-hoc.md` + dòng `Thẻ khoá học:` của kit. Default `all` = mọi ngành. Page chỉ nhận brief đúng thẻ (đồ họa → `do-hoa`). 1 bài cho “toàn bộ page” = chỉ page có thẻ khớp. Sai thẻ → `POST_SKIP ly-do=khong-dung-the`. Ảnh chỉ lấy `attachments/dataset/<id-the>/`.

Kết nối Graph API không đủ.

User chỉ cần 1 dòng chỉ định Fanpage hoặc chọn theo task checklist chiến dịch (ví dụ: Tin học Sao Việt Thủ Đức, Kế toán Sao Việt Bình Dương, AutoCAD Sao Việt Biên Hòa, Royce Shop...).
Thiếu page: tự động lấy target page từ task checklist của chiến dịch đang chạy (30+ Fanpage) **trong số page đã có kit**. Map ngành và chủ đề -> folder + kiểu A/B + kit + chân trang + album Luật C. Không bắt user dán luật.

Trung thu 2026 nếu user không ghi ngày: nghỉ Thứ Sáu 25/09/2026, học lại Thứ Bảy 26/09/2026.

1 goal = 1 page = 1 brief. Không em dash.

**Chân trang = đúng kit của page đang đăng.** Trước khi gọi `fb_page_*`:
```
python "brains/Brain Default/scratch/kit_chan_trang.py" <Page ID>
```
Dán nguyên khối `CHAN_TRANG` vào cuối caption (tên page, địa chỉ cơ sở kit, Hotline/Zalo kit, email kit, web kit).

CẤM dán hotline mặc định `0931 144 858` / `0823 552 558` nếu kit page khác số.
CẤM dán list 12-13 cơ sở nếu kit chỉ 1 chi nhánh (hoặc chỉ Đồng Nai / chỉ Bình Dương).
Plugin chặn đăng (`POST_SKIP ly-do=chan-trang-sai-kit`) khi caption thiếu hotline hoặc mẩu địa chỉ của kit.

## 7. Tự duyệt rồi mới đăng, cấm đốt token (Luật G)

Trước khi gọi tool đăng, tự chấm 6 ô (đọc lại caption + file cover):

1. Caption chuẩn bài chuyển đổi cao (60-120 dòng), đầy đủ 7 phần. Phần cuối = chân trang **của đúng kit page** (địa chỉ + hotline + email + web từ `kit_chan_trang.py`). CẤM list 12 cơ sở khi kit chỉ 1 chi nhánh. CẤM caption tóm tắt dưới 30 dòng. Cover và caption cùng ngành.
2. Bố cục chuẩn vàng Facebook 2026: Album đa dạng 4, 6, 7 hoặc 8 ảnh (Cover luôn là VUÔNG 1:1, ảnh chính 2 VUÔNG 1:1, các ảnh phụ NGANG 3:2) hoặc 1 ảnh poster 1:1 qua fb_page_photo. Safe margin tối thiểu 15% đến 18% từ các mép ngoài, toàn bộ chữ nằm gọn vùng trung tâm, không lỗi chính tả hay đè chữ. Đã tự động chuẩn hóa qua `pick_photos`.
3. Cover gen moi vong nay, khong dung lai file `_xuat` cu. Khong split-navy 2 bai lien tiep.
4. Không logo/hotline brand khác (Bach Khoa, Truong Thinh, Zoom).
5. Album không 2 ảnh cùng cảnh (không file `(1)`, không gốc đã ghép vào cover).
6. Chữ trên cover khớp caption.

Thiếu 1 ô: sửa **tối đa 1 lần** (đổi caption hoặc gen lại 1 cover). Lần 2 vẫn thiếu: **dừng vòng**. Ghi `POST_SKIP ly-do=...`. Không gen lần 3. Không gọi Facebook.

Đăng: **đúng 1 lần** `fb_page_album` hoặc `fb_page_photo`.

- Tool trả `post_id`: ghi `[x]` + post_id ngay; append **chi path goc dataset** vao `_anh-da-dung.md`; **xoa** file cover `_xuat` vua gen. `POST_OK post_id=...`. Khong dung lai anh gen. Khong goi dang lan 2.
- Tool ERROR hoặc không có post_id: `POST_SKIP ly-do=loi-facebook`. CẤM gọi lại tool đăng. CẤM gen thêm. Kết thúc vòng.

CẤM: vòng lặp tìm tool / gen cover / đăng thử nhiều lần. Một vòng = tối đa 1 `image_edit` + 1 lệnh đăng.
