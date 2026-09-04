---
type: wiki
updated: 2026-09-03
---
# Y chu khi dang bai (Royce / Sao Viet)

Doc file nay TRUOC khi soan caption va gen cover. Trai y nay = bai sai.

## Noi dung (Tieu chuan bai viet chuyen doi cao)

- **Do dai & Chieu sau**: Toan bo bai viet khoa hoc (ke ca page chinh lan Royce Shop test) deu phai viet day du, dam tay (60-120 dong), giau suc thuyet phuc nhu bai mau that cua Sao Viet. CAM tuyet doi kieu viet tom tat ngan cun con 10-15 dong.
- **Tieu de / Hook bat buoc**: Moi bai viet bat buoc phai co Tieu de IN HOA noi bat kem emoji nganh o dong 1 (hoac cau hoi trăn tro giat tit, vi du: `🎨 KHOA HOC THIET KE DO HOA TAI TIN HOC SAO VIET...`, `❓ HOC KE TOAN CO KHO KHONG?`, `📐 KHOA HOC VE KY THUAT AUTOCAD 2D & 3D TAI TIN HOC SAO VIET...`). Cam nhay bo vao than bai bang cau tran thuat thieu tieu de.
- **Cau truc 7 phan chuan Sao Viet**:
  1. Tieu de IN HOA kem emoji giat tit.
  2. Noi dau / van de thuc te cua nguoi di lam / sinh vien.
  3. Giai phap khoa hoc tai Tin Hoc Sao Viet.
  4. Cam ket vang doc quyen ("DUY NHAT CHI CO TAI TIN HOC SAO VIET": kem 1-1, hoc den khi thanh thao khong gioi han buoi, thuc hanh chung tu/du an song, ho tro sau khoa...).
  5. Chi tiet noi dung / module ky nang (liet ke ro rang tung phan mem / nghiep vu).
  6. Uu dai hoc phi & qua tang (Giam 20-30% hoc phi, tang tai nguyen...).
  7. CTA, Hotline (093 1144 858 hoac 0823 552 558), va he thong day du 12-13 co so dao tao tai TP.HCM, Binh Duong, Dong Nai, Vung Tau.
- **Dung nganh**: ke toan thi hoa don, so sach, BCTC, Misa; tin hoc thi Word, Excel, PowerPoint, bao cao dong; co khi thi AutoCAD 2D/3D, doc ban ve gia cong; do hoa thi Photoshop, Illustrator, Corel.
- **Cam**: "thoi dai 4.0", "ban co biet", em dash. Chu tren anh khong loi chinh ta.

## Anh & Bố cục Album Facebook (Chuẩn 2026)

- **Quy tắc Cover Banner (BẮT BUỘC HÌNH VUÔNG 1:1)**:
  - Tấm ảnh đầu tiên làm Banner Cover **BẮT BUỘC thiết kế tỷ lệ VUÔNG 1:1** (kích thước 2000x2000 hoặc 1200x1200 px).
  - Khi làm hình vuông, Facebook sẽ ghim trọn vẹn ở ô chính bên trái, KHÔNG BAO GIỜ BỊ CẮT XÉN 2 bên mép như banner ngang 16:9, hiển thị trọn 100% tiêu đề, logo, ưu đãi và hotline cực kỳ sắc nét.
  - Safe margin: 15-18% từ các mép ngoài.

- **Bố cục Album đa dạng chuẩn Facebook 2026 (4, 6, 7, 8 ảnh)**:
  - **Bố cục nhiều hơn 5 ảnh (6, 7, 8 ảnh...) - Chuẩn vàng Facebook 2 cột**:
    - **Cột trái (2 ảnh vuông 2000 x 2000)**:
      - `photos[0]` (Ảnh chính 1): Banner Cover VUÔNG 1:1 (2000x2000).
      - `photos[1]` (Ảnh chính 2): Ảnh lớp học đẹp nhất crop VUÔNG 1:1 (2000x2000).
    - **Cột phải (3 ảnh ngang 2000 x 1330 ~ tỷ lệ 3:2)**:
      - `photos[2]` (Ảnh phụ 1): Ảnh ngang 2000x1330.
      - `photos[3]` (Ảnh phụ 2): Ảnh ngang 2000x1330.
      - `photos[4]` (Ảnh phụ 3): Ảnh ngang 2000x1330 (tự động hiện huy hiệu `+N` cho các ảnh tiếp theo: `+2`, `+3`...).
    - **Cân bằng hoàn hảo**: Tổng chiều cao cột trái (2000 + 2000 = 4000) bằng khít cột phải (1330 + 1330 + 1330 = 3990), không bị so le, không khoảng trống.
  - **Bố cục 4 ảnh**: Cả 4 ảnh đều VUÔNG 1:1 (2000x2000) -> Facebook hiển thị lưới 2x2 gồm 4 ô vuông bằng nhau hoàn mỹ.
  - **TUYỆT ĐỐI KHÔNG DÙNG BANNER NGANG 16:9 KHI ĐĂNG NHIỀU ẢNH**: Banner ngang 16:9 khi vào album sẽ bị Facebook ép thành hình vuông/hình đứng làm mất 40% chữ 2 bên.
  - **Tự động chuẩn hóa ảnh**: Lệnh `python "brains/Brain Default/scratch/hub_call.py" pick_photos <folder> <cover_path> random` sẽ tự động chọn ảnh và chuẩn hóa kích thước/tỷ lệ đúng chuẩn Facebook 2026 trước khi đăng.

- **Cover chuẩn đẹp - Xoay 2 kiểu cốt lõi (ĐÃ XOÁ STYLE 3 NEON DO LỖI CHỮ & XẤU)**:
  1. **Kiểu 1 - Poster mockup studio 1:1 (chuẩn như mẫu đồ họa `mau-poster-do-hoa.png`)**: Học viên/chuyên gia tươi tắn bên laptop + icon phần mềm 3D bay nổi khối + tiêu đề to rõ nổi bật trên nền xanh nhận diện Sao Việt + badge ưu đãi bo góc + footer hotline. Chữ không đè nhau.
  2. **Kiểu 2 - Ảnh thật lớp học 1:1 + Khung thương hiệu**: Kết hợp ảnh lớp học thật từ dataset + khung chữ thanh dưới sắc nét, logo Sao Việt, không che mặt học viên.
  *(Style 3 Neon viền mạch điện tối tăm đã xoá bỏ hoàn toàn khỏi hệ thống).*

- **Logo**: `chung/thsv-logo-2025.png`. Cấm Bach Khoa, Truong Thinh, Zoom.

## Cach ra lenh ngan (copy)

`Ve ky thuat AutoCAD Royce Shop. Caption day du chuyen doi 7 phan, co cam ket vang, module, uu dai va 12 co so. Cover mockup 1:1 vuong dung nganh co khi, chu nam trong safe margin.`

