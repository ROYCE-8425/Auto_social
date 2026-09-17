# PROMPT GEMINI — Tài liệu GitHub mã nguồn mở (contest, không gắn 1 doanh nghiệp)

Dán từ **BẮT ĐẦU**. Mục tiêu: repo `ROYCE-8425/Auto_social` nhìn như **OSS chuyển đổi số SME**, đứng trên **Javis OS (MIT)**. Cấm thương hiệu trung tâm đào tạo / MST trên README, landing copy, CONTRIBUTING.

Không viết lại engine Javis. Không commit secret (`page_tokens.json`, PostPeer key, `.env`).

---

## BẮT ĐẦU

### 0. Tên và attribution

- **Tên sản phẩm (UI + README):** `Javis Ops` (lớp vận hành) trên **Javis OS**.
- Repo GitHub: giữ `Auto_social`.
- LICENSE: **MIT**. Giữ copyright Nguyễn Minh Quý (Javis OS). Thêm dòng:  
  `Portions Copyright (c) 2026 contributors of Auto_social / Javis Ops`  
  Không xóa LICENSE gốc.
- File mới `NOTICE.md` (ngắn): fork/dựa [Javis OS](https://github.com/blogminhquy/javis-os), MIT; lớp Care, `/ops`, TikTok PostPeer, CRM đa brand là phần mở rộng.

### 1. README.md (tiếng Việt, trên cùng)

Thay **phần đầu** README hiện tại (đừng xóa hết hướng dẫn cài Javis phía dưới nếu còn đúng). Cấu trúc:

```
# Javis Ops
Lớp vận hành mạng xã hội cho SME, tự host, mã nguồn mở.
Đứng trên Javis OS (MIT).

## Đây là gì
Não AI (Javis) chạy nền. Nhân viên dùng /ops. Chủ máy dùng /app.

## Ba cửa
| URL | Ai | Việc |
| / | công chúng | Landing |
| /ops | CSKH, quản lý | Hộp thư, CRM, việc, TikTok (xem) |
| /app | chủ máy | Console, MCP, loop, Đăng thử TikTok |

## Tính năng lớp Ops (chỉ liệt kê CÁI ĐÃ CÓ)
- Đăng Fanpage Graph (album, kit, token page)
- Care: kéo comment + IB Messenger, phân loại rules-first, nháp, CRM
- Phạm vi: tất cả page / theo brand / 1 page
- Công tắc: kéo comment, kéo IB, tự trả lời comment, tự IB (mặc định nháp)
- RBAC: staff / manager / owner; staff 403 /app
- TikTok: PostPeer BYO key, carousel 9:16, autoAddMusic, /tiktok-media
- Brand kit markdown (nhiều thương hiệu, không khoá 1 shop)

## Không phải
- SaaS khóa vendor
- Thay Facebook Graph bằng PostPeer
- Chatbot full-brain cho khách

## Nhanh
Docker / VPS như Javis. Demo: trannhuy.online (nếu còn public)

## Bảo mật
Không commit page_tokens, POSTPEER_API_KEY, settings.json secret.
scripts/connect_postpeer.py đọc env.

## Attribution
Javis OS © Nguyễn Minh Quý, MIT.
```

README.en.md: bản Anh **cùng nội dung**, không Google Translate sáo.

Cấm trong README: tên trung tâm, MST, hotline shop, “giáo trình”, 13 cơ sở.

Demo brand trong docs nội bộ được: **Game BSN** như ví dụ kit, không phải tên sản phẩm.

### 2. File GitHub chuẩn

| File | Việc |
|---|---|
| `LICENSE` | MIT + dòng copyright fork |
| `NOTICE.md` | Javis OS + phần mở rộng |
| `SECURITY.md` | Báo lỗ hổng; cấm dán token lên issue |
| `CONTRIBUTING.md` | PR vào `ROYCE-8425/Auto_social` `main`; test `pytest tests/python/test_ops_*.py test_fanpage_care_*.py test_tiktok_*.py test_landing.py`; không PR chứa secret |
| `.github/ISSUE_TEMPLATE` | bug / feature (tuỳ chọn, ngắn) |
| `docs/29-ops-dashboard.md` | Đổi tiêu đề Javis Ops, xóa tên trung tâm |
| `CHANGELOG.md` | 1 mục: lớp Ops, Care, /ops, TikTok PostPeer, RBAC — không liệt kê 50 commit |

### 3. Landing `website/index.html`

Đã rebrand Javis Ops. Rà còn sót tên DN thì xóa. Hero: đa thương hiệu SME, không 1 trường.

### 4. .gitignore (kiểm, đừng nuốt code)

Đảm bảo ignore: `server/settings.json`, `**/page_tokens.json`, `.env`, `ops/node_modules`, `*.sqlite3`. **Không** ignore `ops/dist` nếu VPS deploy từ git (nếu đang commit dist thì giữ).

### 5. Cấm

- Rewrite toàn bộ README Javis thành brochure 1 shop.
- Xóa hướng dẫn Docker/engine (vẫn cần để tự host).
- Commit key. Fake badge “10k stars”.
- Đổi LICENSE sang proprietary.

### 6. Done

Clone repo → README 30 giây hiểu: OSS, Javis OS, 3 cửa, Care, TikTok optional. LICENSE MIT + NOTICE. Không tên DN trên trang GitHub. `pytest` tài liệu không bắt live Graph.

## HẾT
