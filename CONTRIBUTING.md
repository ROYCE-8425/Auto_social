# Đóng góp cho Sèo Trum (Auto_social)

Cảm ơn bạn đã muốn đóng góp. Repo này nhận Pull Request từ **fork** - bạn không cần quyền
ghi trực tiếp, chỉ cần fork về tài khoản của mình, code, rồi mở PR nhắm vào nhánh `main` của repo `ROYCE-8425/Auto_social`.

## Quy trình

1. **Fork** repo này (`https://github.com/ROYCE-8425/Auto_social`), clone bản fork về máy.
2. Tạo nhánh mới đặt tên gợi nhớ việc đang làm (vd `fix-inbox-realtime`, `them-template-care`).
3. Code, rồi tự chạy test trước khi mở PR (xem mục Test bên dưới) - PR chưa chạy test
   local dễ vướng lỗi vặt mà CI mới bắt được.
4. Mở PR nhắm vào `main` của repo `ROYCE-8425/Auto_social`, mô tả rõ **vì sao** cần
   thay đổi này, không chỉ **cái gì** đã đổi (cái gì thì đọc diff là thấy).
5. CI tự chạy. PR xanh + được duyệt mới merge - người giữ repo sẽ xem qua từng PR.

## Phạm vi dự án

Repo này là lớp nghiệp vụ social operations được xây trên nền Javis OS. Khi mở PR, vui lòng ghi rõ thay đổi thuộc nhóm nào:

- Nền tảng/chung: chỉnh sửa runtime, MCP, auth, cấu hình hoặc triển khai.
- Lớp Sèo Trum: `/ops`, Fanpage Care, CRM, lead scoring, Social Channels Hub, TikTok/PostPeer, tài liệu cuộc thi.
- Tài liệu/open source: README, NOTICE, SECURITY, CONTRIBUTING, checklist, issue template.

Các thay đổi lớn chạm vào nền tảng chung nên mở Issue trước để thống nhất phạm vi.

## ⚠️ Nguyên tắc bảo mật bắt buộc

- **Tuyệt đối KHÔNG commit hoặc mở PR chứa token, mật khẩu, API key:**
  - Không commit `page_tokens.json`, `settings.json`, PostPeer API Key, Gemini/OpenAI key, `.env`, `server/.secret_key`, `server/.hub_token`, `*.sqlite3`, `*.db`, log hội thoại hoặc dữ liệu khách hàng thật.
  - Luôn kiểm tra `git status` và `git diff` trước khi commit.
- Mọi vấn đề bảo mật xin vui lòng làm theo hướng dẫn trong [SECURITY.md](SECURITY.md), không mở Issue công khai.

## Chạy test trước khi mở PR

```bash
pip install -r requirements.txt

# Chạy kiểm tra kiểm thử chuẩn của repo:
python tests/run.py --py

# Chạy nhanh bộ kiểm thử lớp vận hành Javis Ops (RBAC, Care, TikTok, Landing):
pytest tests/python/test_ops_rbac.py tests/python/test_ops_routes.py tests/python/test_fanpage_care_policy.py tests/python/test_fanpage_care_store.py tests/python/test_fanpage_care_classify.py tests/python/test_landing.py tests/python/test_postpeer_tiktok.py tests/python/test_agent_workflow_tiktok.py
```

## Quy ước code

- Không thêm tính năng/refactor ngoài phạm vi PR đang làm.
- Comment chỉ viết khi giải thích **vì sao** (constraint ẩn, workaround), không lặp lại cái code đã nói (**cái gì**).
- `CHANGELOG.md`: vài gạch đầu dòng, nói người dùng **thấy gì khác**, không liệt kê hàng chục commit rác.
- Giữ phong cách tối giản, nhẹ, dễ tự host trên VPS khiêm tốn.
- Giữ attribution Javis OS trong README/NOTICE/LICENSE khi chỉnh sửa tài liệu pháp lý.
- Với giao diện `/ops`, ưu tiên luồng làm việc thật của nhân viên/quản lý hơn layout trang giới thiệu.

## Báo lỗi / đề xuất tính năng

Vui lòng mở **Issue** trên GitHub để mô tả lỗi hoặc thảo luận giải pháp trước khi viết các tính năng lớn hoặc đổi kiến trúc hệ thống.
