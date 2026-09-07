---
name: Đăng bài Facebook
description: "Co anh dataset: album tat ca goc (cam 1 anh, cam gen). Khong anh lien quan: moi gen 1 tam."
group: Marketing
---

# Đăng bài Facebook

Doc `wiki/brand-kits/_y-chu-dang-bai.md` va `_quy-trinh-dang-bai.md` truoc. Moi bai = dung 1 kit page (logo/mau/font/giong/chan trang). Khong dung kit page khac. Engine viec nen: **Gemini API key** (khong Antigravity/`agy`, khong Gemini CLI, khong bat ChatGPT).

**QUY TẮC CỐT TỬ CỦA WORKER (CẤM HỎI NGƯỜI DÙNG):**
Kanban cấm tuyệt đối worker đặt câu hỏi cho người dùng (như "Bạn có muốn...", "Có nên tiếp tục..."). Nếu hỏi, Kanban sẽ lập tức chặn việc ("Worker hỏi thay vì đăng"). Nhiệm vụ phải tự chủ hoàn thành từ đầu đến cuối và kết thúc bằng kết quả chứa `post_id` sau khi đăng lên Facebook. Nếu tạo ảnh AI có bất kỳ vấn đề gì, hệ thống tự động dùng ảnh thật từ dataset dán logo thương hiệu Sao Việt làm cover để đăng ngay, tuyệt đối không được dừng lại hỏi.

**Album 7/3.** Anh 1 = banner quang cao: gen tu 1 raw dung the + logo kit, HOAC gen AI full van kem logo kit. Toi da 3 gen. Con lai anh raw dataset. Cover `_xuat/`.
Cover mac dinh = gen 1 lan tu **1 anh raw dataset + logo kit** (file `attachments/dataset/chung/thsv-logo-2025.png` hoac logo trong kit page). Tool: `javis_search_tools` roi `javis_run_tool` `gemini_generate_image` (Google Imagen 3). **Bat buoc** dua 2 anh tham chieu: (1) anh lop/raw, (2) file logo - khong gen logo bang tri nho. Luu `_xuat/`. Anh 2..N = anh goc dataset (qua `pick_photos`). Cấm gen 2+ poster. Cấm `agy`. Facebook: `fb_page_album` / `fb_page_photo`.

## 1. Chọn folder dataset theo brief (Luật A)

| Chữ trong brief / thẻ kit                 | Folder (id đúng trên đĩa)                          |
| ----------------------------------------- | -------------------------------------------------- |
| Word, Excel, văn phòng, MOS, AI văn phòng | `attachments/dataset/tin-hoc _ai/` (`tin-hoc _ai`) |
| AutoCAD, SolidWorks, vẽ kỹ thuật          | `attachments/dataset/ve-ky-thuat/` (`ve-ky-thuat`) |
| Kế toán, chứng từ, sổ sách                | `attachments/dataset/ke-toan/`                     |
| Photoshop, Illustrator, đồ họa            | `attachments/dataset/do-hoa/`                      |
| Logo only                                 | `attachments/dataset/chung/` (chỉ watermark)       |

CẤM tìm folder cũ `tin-hoc/`, `co-khi/`, `ai/`, `marketing/`, `tre-em/`, `tieng-han/` - đã gộp/xoá. Không có folder → chọn thẻ khác trong kit, **không** `[[NEEDS_INPUT]]`. Caption tự viết từ skill `viet-bai-facebook`; không cần file giáo trình trong brain.

Kit page có **nhiều ngành**: dòng `Folder anh (dataset): tin-hoc, ke-toan, co-khi`. Brief chọn 1 ngành trong list đó. Không khóa 1 folder/page.

Đếm file jpg/png/webp trong folder ngành (không tính `chung`, `_mau`, `_xuat`). Đó là ảnh liên quan.

Sau post_id: chi append path **anh goc dataset** vao `_anh-da-dung.md` (khong ghi file `_xuat`). Uu tien goc chua dung; het goc moi thi dung lai goc (khong rut xuong 1 tam).

**Anh gen AI khong tai su dung:** CAM lay bat ky file trong `_xuat/` cua vong truoc lam cover/album. Cover phai gen MOI trong vong nay (neu can). Co post_id: **xoa** file cover vua gen trong `_xuat/` (Facebook da co ban). Giu nguyen anh raw trong `tin-hoc _ai/`, `ke-toan/`, `do-hoa/`, `ve-ky-thuat/`. CẤM folder `tin-hoc/` (đã gộp thành `tin-hoc _ai`).

## 2. Khi nào gen, khi nào dùng ảnh có sẵn (Luật B)

Liệt kê file ảnh trong folder ngành. Gọi N = số file. Đọc `_mau/bo-cuc.md` (GIỮ / BỎ).

**Cover (ảnh đầu) xoay 2 kiểu cốt lõi (ĐÃ XOÁ STYLE 3 NEON)** (đọc `_mau/bo-cuc.md`). Cấm lặp 2 bài liên tiếp cùng kiểu. CẤM mở `_xuat` cũ.

- **Kiểu 1 Poster mockup studio 1:1 (chuẩn như `mau-poster-do-hoa.png`):** Thiết kế tỷ lệ VUÔNG 1:1 (2000x2000 hoặc 1200x1200 px). Hình ảnh học viên/chuyên gia trẻ trung ngồi bên laptop + icon 3D phần mềm bay nổi khối (Word, Excel, AutoCAD, Misa, Ps...) + tiêu đề to rõ nền xanh nhận diện Sao Việt + badge ưu đãi vàng "ƯU ĐÃI 30% HỌC PHÍ - KÈM 1-1" + footer hotline. Chữ không đè nhau, safe margin 15-18%.
- **Kiểu 2 Ảnh gốc 1:1 + Khung thương hiệu:** Kết hợp ảnh lớp học thật từ dataset + khung chữ thanh dưới sắc nét (mẫu A-full 1:1), logo Sao Việt, không che mặt học viên.
  _(Style 3 Neon viền mạch điện tối tăm đã xoá bỏ hoàn toàn khỏi hệ thống)._

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

N>=2: chỉ `fb_page_album` 1 lần. N<=1: `fb_page_photo` 1 lần. **CẤM `fb_page_post`** (chỉ chữ, không ảnh). Không thử cả relative và absolute.
CẤM gọi `fb_page_delete` trừ khi người dùng ra lệnh rõ ràng kèm đúng post_id cần xóa. Tuyệt đối không tự đăng thử rồi tự xóa.

## 6. Goal ngắn, tự bung (Luật F)

**CẤM đăng page chưa có Brand Kit.** Trước khi gọi `fb_page_*`: đọc `wiki/brand-kits/*.md`, chỉ đăng page có file kit và dòng `Page ID:` khớp. Không có kit → `POST_SKIP ly-do=chua-co-brand-kit`.

**CẤM đăng sai thẻ.** Đọc `_the-khoa-hoc.md` + dòng `Thẻ khoá học:` của kit. Default `all` = mọi ngành. Page chỉ nhận brief đúng thẻ (đồ họa → `do-hoa`). 1 bài cho “toàn bộ page” = chỉ page có thẻ khớp. Sai thẻ → `POST_SKIP ly-do=khong-dung-the`. Ảnh chỉ lấy `attachments/dataset/<id-the>/`.

Kết nối Graph API không đủ.

User chỉ cần 1 dòng chỉ định Fanpage hoặc chọn theo task checklist chiến dịch (ví dụ: Tin học Sao Việt Thủ Đức, Kế toán Sao Việt Bình Dương, AutoCAD Sao Việt Biên Hòa, Royce Shop...).

**TỰ ĐỘNG KHỚP MỜ (FUZZY MATCH) BRAND KIT & TRANG:**

- Khi brief hoặc user chỉ định tên Trang (ví dụ: "page royce", "thủ đức", "cad biên hòa", "kế toán quận 7"):
  - BẮT BUỘC tự động khớp mờ (fuzzy match) tìm file kit tương ứng trong `wiki/brand-kits/` (ví dụ: `royce` -> `royce-shop.md`, `thủ đức` -> kit Thủ Đức).
  - Khớp theo ngành học: nếu brief chỉ ghi địa danh chung chung (vd "quận 7"), đối chiếu ngành trong brief (tin học / kế toán / autocad / đồ họa) để chọn đúng cơ sở.
  - Chạy ngay lệnh tìm tự động:
    ```
    python "brains/Brain Default/scratch/kit_tim.py" "<tên_page_hoặc_từ_khóa>"
    ```
    hoặc:
    ```
    python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py" --page "<tên_page_hoặc_từ_khóa>"
    ```
    Lệnh này sẽ tự động phân giải, trả về đúng Page ID, slug, file kit và toàn bộ khối CHAN_TRANG chuẩn.
  - **TUYỆT ĐỐI CẤM HỎI LẠI TRONG KANBAN WORKER:** Kanban là hệ thống worker chạy ngầm (headless). Người dùng không ngồi trực chat. Nghiêm cấm hỏi các câu như "Tôi không tìm thấy royce.md, bạn có muốn dùng royce-shop.md không?". Hỏi thay vì làm sẽ bị hệ thống phát hiện và BLOCK ngay lập tức. Hãy tự động chọn kit điểm cao nhất, ghi log lý do và tiến hành đăng luôn.

Thiếu page: tự động lấy target page từ task checklist của chiến dịch đang chạy (30+ Fanpage) **trong số page đã có kit** hoặc chạy `python "brains/Brain Default/skills/dang-bai-facebook/scripts/pick_next_fanpage.py"`. Map ngành và chủ đề -> folder + kiểu A/B + kit + chân trang + album Luật C. Không bắt user dán luật.

Trung thu 2026 nếu user không ghi ngày: nghỉ Thứ Sáu 25/09/2026, học lại Thứ Bảy 26/09/2026.

1 goal = 1 page = 1 brief. Không em dash.

**Chân trang = đúng kit của page đang đăng.** Trước khi gọi `fb_page_*`:

```
python "brains/Brain Default/scratch/kit_chan_trang.py" <Page ID hoặc từ khóa page>
```

Dán nguyên khối `CHAN_TRANG` (script đã tự tách **mỗi cơ sở một dòng** và hỗ trợ cả từ khóa mờ). CẤM copy chuỗi `A | B | C` vào caption. Plugin chặn `dia-chi-mot-dong`.

CẤM dán hotline mặc định `0931 144 858` / `0823 552 558` nếu kit page khác số.
CẤM dán list 12-13 cơ sở nếu kit chỉ 1 chi nhánh (hoặc chỉ Đồng Nai / chỉ Bình Dương).
Plugin chặn khi **thiếu hẳn** hotline (9 số cuối) hoặc **không có 1 mẩu địa chỉ nào** của kit. Sai dấu/viết tắt/thiếu 1 cụm thì vẫn đăng. Email không bắt. Royce Shop = page test, **vẫn** chặn caption cụt và địa chỉ một dòng `|`.

`chan-trang-sai-kit` / `khong-retry=1`: POST*SKIP **1 lần rồi DỪNG**. CẤM sửa caption 20 lần, CẤM `[[NEEDS_INPUT]]`, CẤM rollback, CẤM gọi `fb_page*\*` lại.

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
- `khong-retry=1` / `chan-trang-sai-kit`: dừng task (blocked 1 lần). CẤM 20 lần chạy. CẤM NEEDS_INPUT.

CẤM đăng thử nhiều lần. Có `NEXT=1` thì đọc **đúng 1 kit** `wiki/brand-kits/<kit>` (địa chỉ/hotline page đó), không đọc 56 kit, không `fb_pages_list`. **Bắt buộc** soạn theo `viet-bai-facebook` đủ 7 phần **60-120 dòng** - cấm cắt caption để tiết kiệm token. Plugin chặn bài dưới 45 dòng (`caption-ngan`). Ngành = `_the-khoa-hoc.md`. Ảnh 1 = poster gen `_xuat/`. CẤM `fb_page_post`.

## 8. Quy chuẩn Cover Banner & Tỷ lệ sinh ảnh 7 / 3

Nhằm đảm bảo hình ảnh chân thực, thu hút người xem và đạt tỷ lệ chuyển đổi cao nhất cho các khóa học Tin học Sao Việt, hệ thống áp dụng cơ chế sinh Cover tỷ lệ **7 / 3**:

### Tỷ lệ phân bổ khi tạo Cover

- **70% Kiểu 2 (Authentic Classroom Banner - Khuyên dùng & Mặc định chiếm đa số):**
  - Sử dụng ảnh chụp lớp học thật 100% từ kho dataset (`attachments/dataset/<ngành>/`).
  - Kết hợp dải đồ họa thương hiệu Solid Deep Navy (`#0B2341`), logo Sao Việt đặt trên thẻ bo góc nổi khối 3D, tiêu đề và điểm nổi bật in hoa sắc nét (màu trắng và vàng hoàng gia).
  - Tuyệt đối không bao giờ đè chữ lên mặt/lưng học viên hoặc màn hình máy tính.
  - Font chữ 100% TrueType Unicode (Arial Bold / Segoe UI), tự động ngắt dòng và co dãn thông minh, không lỗi font, không lệch khung hay tràn viền.
- **30% Kiểu 1 (AI 3D Poster):**
  - Dựng poster giáo dục 3D hiện đại sinh qua Google Imagen / Gemini API, có dán logo Sao Việt chuẩn pixel.
  - Nếu Google API gặp lỗi hạn mức, hết quota hoặc model không phản hồi: Hệ thống **tự động cứu hộ 100% về Kiểu 2**, đảm bảo tiến trình đăng bài không bao giờ bị gián đoạn.

### 5 Mẫu Layout Agency Đồ Họa Đa Dạng (Kiểu 2)

1. `split_right` (Chuẩn theo ảnh mẫu tham chiếu): Cột trái (50%) là ảnh lớp học thật, cột phải (50%) là panel xanh thương hiệu với logo góc trên, tiêu đề lớn, gạch phân cách vàng kim, 3 điểm nổi bật và hotline.
2. `split_left`: Đảo vị trí panel sang bên trái, ảnh thật bên phải nhằm tạo sự phong phú giữa các bài viết trên cùng 1 Fanpage.
3. `bottom_bar`: Ảnh chụp lớp học góc rộng sáng sủa chiếm 62% phía trên, dải panel thương hiệu solid navy chiếm 38% chân trang cùng các huy hiệu viên thuốc bo tròn hiện đại.
4. `floating_card`: Ảnh lớp học tràn nền, một card thông tin bo góc nổi khối 3D với viền vàng ánh kim và bóng đổ mềm mại.
5. `diagonal_slice`: Đường cắt vát chéo góc công nghệ hiện đại, tạo cảm giác chuyển động và tràn đầy năng lượng.

### Cách gọi lệnh và cấu hình

- Tự động trong tool `gemini_generate_image`: Mặc định quay xác suất 70% Kiểu 2 và 30% Kiểu 1.
- Nếu prompt chứa `"kiểu 2"`, `"kieu 2"`, `"ảnh thật"`, `"dataset"`, `"banner"`: Hệ thống sinh 100% Kiểu 2.
- Nếu prompt chứa `"kiểu 1"`, `"kieu 1"`, `"3d"`, `"mockup"`, `"studio"`: Hệ thống sinh Kiểu 1 (fallback Kiểu 2 nếu lỗi mạng/quota).
- Sinh thủ công qua script:
  ```bash
  python "brains/Brain Default/scratch/make_square_cover.py" tinhoc --kieu2
  python "brains/Brain Default/scratch/make_square_cover.py" ketoan --kieu2 --template split_right
  ```
