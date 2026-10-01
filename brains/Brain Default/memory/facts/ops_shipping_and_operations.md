# Vận Hành Đơn Hàng & Vận Chuyển Giao Hàng Nhanh (GHN)

## 1. Quy trình xử lý đơn hàng (Order Lifecycle)
1. **Chờ xác nhận (`pending`):** Đơn hàng mới ghi nhận từ Inbox/Fanpage hoặc nhân viên tư vấn tạo.
2. **Đã xác nhận (`confirmed`):** Nhân viên xác nhận thông tin nhận hàng, số điện thoại và số tiền COD.
3. **Đang giao hàng (`shipping`):** Đơn đã được bàn giao cho đối tác vận chuyển Giao Hàng Nhanh (GHN) và có mã vận đơn theo dõi.
4. **Đã hoàn thành (`delivered`):** Khách nhận hàng thành công, hệ thống đối soát tiền COD và hoàn tất đơn.
5. **Đã hủy (`cancelled`):** Khách hủy đơn hoặc hoàn trả do không liên lạc được.

## 2. Kết nối đối tác vận chuyển Giao Hàng Nhanh (GHN)
- **Tích hợp:** `server/ops_shipping.py` & API đồng bộ tự động `POST /ops/orders/{order_id}/sync-shipment`.
- **Mã vận đơn:** Bắt đầu bằng tiền tố `GHN...` (ví dụ: `GHNMOCK-HCM-001`, `GHNMOCK-BD-002`).
- **Tra cứu hành trình:** Hệ thống tự động ghi nhận thời điểm lấy hàng, đang trung chuyển và giao thành công kèm nhật ký kiểm toán (Audit log).

## 3. Chính sách hỗ trợ & Chăm sóc khách hàng
- **Cơ chế Human Takeover:** Khi nhân viên ca trực vào chat trực tiếp với khách hàng trên Messenger/Zalo, AI Javis tự động tạm dừng phản hồi trong 24 giờ để không tranh lời nhân viên. Sau khi hỗ trợ xong, nhân viên có thể bấm "Javis nhận lại" (Release Takeover).
- **Quy tắc bảo mật thông tin:** Số điện thoại khách hàng hiển thị cho nhân viên tư vấn phải được ẩn 3 số giữa (ví dụ: `0912***456`) để bảo vệ dữ liệu khách hàng.
