---
name: "Xử lý token Meta Facebook an toàn"
description: "Tư vấn và kiểm tra token Meta/Facebook mà không lộ secret, ưu tiên OAuth và Page Token đúng chuẩn."
group: "Facebook"
origin: javis-learned
status: active
created: 2026-09-09
---
## Khi nào dùng

Dùng khi người dùng hỏi về App ID, App Secret, User Access Token, Page Access Token, quyền đăng Fanpage, lỗi app bị khóa, hoặc muốn nạp token Facebook vào Javis.

Dùng khi người dùng dán token hoặc secret vào chat và yêu cầu Javis cấu hình thay.

## Chuẩn bị

Đọc trạng thái vault hoặc file đang mở nếu prompt có block FILE ĐANG MỞ.

Không in lại App Secret, access token, refresh token hoặc token dạng dài trong câu trả lời.

Nếu có tool đọc kết nối Facebook, chỉ dùng để kiểm trạng thái connector, page list hoặc lỗi API. Không tự ghi token vào file vault.

## Cách chạy

1. Xác định người dùng đang nói về loại khóa nào: App ID, App Secret, User Access Token hay Page Access Token.
2. Nếu người dùng gửi secret/token, coi là dữ liệu nhạy cảm và không nhắc lại nguyên văn.
3. Kiểm tra connector Facebook hiện tại nếu có tool đọc an toàn.
4. Nếu connector yêu cầu OAuth, giải thích rằng Javis phải lấy Page Token qua OAuth thay vì hardcode token thủ công.
5. Nếu API báo app bị xóa, app bị khóa hoặc app không hợp lệ, kết luận lỗi nằm ở Meta App trước, không phải chỉ ở Page Token.
6. Với nhu cầu scale nhiều Fanpage, khuyến nghị chia nhiều Meta App/connection theo cụm page và giãn lịch đăng.

## Quy trình

Phân biệt luồng chuẩn:

```text
Meta App -> User Access Token -> Page Access Token -> đăng bài lên Fanpage
```

Nếu người dùng muốn Page Access Token riêng, nói rõ Page Token vẫn phụ thuộc vào Meta App đã sinh ra nó. Nếu app bị khóa hoặc bị xóa, Page Token từ app đó có thể không giải quyết được.

Ưu tiên cấu hình qua Javis Connections:

```text
Javis > Kết nối > Facebook Trang (tự tạo app - Graph API) > App ID + App Secret > OAuth > chọn Fanpage
```

Với chạy số lượng lớn, đề xuất chia nhóm khoảng 10-20 page cho mỗi app/connection nếu Meta bắt đầu bóp hoặc khóa theo app.

## Bẫy

Không khuyên hardcode token vào vault.

Không nói Page Token hoàn toàn độc lập với App.

Không hứa đã nạp token nếu không có tool ghi connection/token trả về thành công.

Không ghi nhớ hoặc xuất lại token/secret người dùng đã dán.

## Kiểm chứng

Sau khi cấu hình, kiểm tra connector có enabled, trạng thái ổn, quyền đủ để đăng bài, và page cần đăng xuất hiện trong danh sách page.

Nếu đăng bài cần thực thi ngoài Facebook, connector phải có quyền phù hợp, không chỉ readonly.
