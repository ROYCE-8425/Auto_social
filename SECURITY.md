# Chính sách Bảo mật (Security Policy)

## Phiên bản được hỗ trợ

| Phiên bản | Hỗ trợ bảo mật     |
| --------- | ------------------ |
| latest    | :white_check_mark: |

---

## ⚠️ Nguyên tắc an toàn & Cấm lộ thông tin bí mật

1. **Tuyệt đối KHÔNG đăng token / API key / mật khẩu lên GitHub Issues hoặc Pull Requests công khai.**
   * Bao gồm nhưng không giới hạn: Meta Graph User/Page Access Tokens (`page_tokens.json`), PostPeer API Key, OpenAI/Claude/Gemini API keys, `.env`, `settings.json`.
2. **Kiểm tra trước khi commit:**
   * Hệ thống đã cấu hình `.gitignore` chặn các file nhạy cảm. Luôn chạy `git status` trước khi commit để đảm bảo không vô tình thêm file bí mật vận hành vào git.
3. **Biến môi trường:**
   * Sử dụng biến môi trường hoặc cấu hình qua giao diện bảo mật của Javis thay vì hardcode thông tin bí mật vào mã nguồn.

---

## Báo cáo lỗ hổng bảo mật

Nếu bạn phát hiện lỗ hổng bảo mật hoặc rò rỉ thông tin đăng nhập:
1. **Không mở Issue công khai.**
2. Vui lòng liên hệ riêng với quản trị viên qua tính năng **GitHub Private Vulnerability Reporting** hoặc qua email của người duy trì repository.
3. Cung cấp mô tả chi tiết, các bước tái hiện và mức độ ảnh hưởng ước tính.
4. Đội ngũ sẽ xác minh và khắc phục trong thời gian sớm nhất trước khi công bố thông tin bản vá.
