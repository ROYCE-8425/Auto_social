"""Hợp đồng UI cho tên giọng thân thiện và wizard tên miền.

Chạy:
    .venv/Scripts/python.exe server/test_domain_setup_ui.py
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
from pathlib import Path


INDEX = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
BRANDING = (ROOT / "dashboard" / "branding.js").read_text(encoding="utf-8")
# Đây là test HỢP ĐỒNG trên mã nguồn: nó khẳng định backend có xử lý một số tình huống,
# bằng cách tìm chuỗi trong nguồn. Từ 0.9.243 các nhóm route được bóc dần khỏi main.py sang
# routes/, nên đọc mỗi main.py là đỏ oan mỗi lần bóc một khối. Ghép cả main.py lẫn routes/
# để test bám vào HÀNH VI CÒN TỒN TẠI chứ không bám vào chỗ nó đang nằm.
MAIN = "\n".join(
    [(SERVER / "main.py").read_text(encoding="utf-8")]
    + [p.read_text(encoding="utf-8") for p in sorted((SERVER / "routes").glob("*.py"))]
)
HOSTINGER = (ROOT / "docker-compose.hostinger.yml").read_text(encoding="utf-8")
VPS = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
DOC = (ROOT / "docs" / "15-thuong-hieu-ten-mien.md").read_text(encoding="utf-8")

fails = []


def check(name: str, condition: bool) -> None:
    if condition:
        print(f"PASS: {name}")
    else:
        print(f"FAIL: {name}")
        fails.append(name)


check("UI đổi HoaiMy thành Ngọc Thu nhưng giữ mã Edge",
      "<strong>Ngọc Thu</strong>" in INDEX and 'value="vi-VN-HoaiMyNeural"' in INDEX)
check("UI đổi NamMinh thành Nam Minh nhưng giữ mã Edge",
      "<strong>Nam Minh</strong>" in INDEX and 'value="vi-VN-NamMinhNeural"' in INDEX)
check("card tên miền có hành động lưu và kiểm tra rõ ràng", "Lưu &amp; kiểm tra" in INDEX)
check("card có hai link tài liệu", "docs/15-thuong-hieu-ten-mien.md" in INDEX and "DEPLOY.md" in INDEX)
check("wizard có ba bước và nút sao chép", "1. Lưu tên miền" in BRANDING and
      "2. Trỏ DNS về VPS" in BRANDING and "3. Bật HTTPS" in BRANDING and "data-copy" in BRANDING)
check("wizard có nhánh Hostinger riêng", "Kích hoạt route HTTPS trên Hostinger" in BRANDING and
      "DOMAIN_NAME=" in BRANDING and "Redeploy" in BRANDING)
check("backend trả metadata môi trường cho UI", all(x in MAIN for x in (
      '"deployment_target"', '"route_domain"', '"ui_can_enable_ssl"', '"requires_redeploy"')))
check("backend không giả vờ sửa được Traefik Hostinger", "Hostinger quản lý HTTPS bằng Traefik" in MAIN)
check("compose Hostinger khai báo target và route hiện tại",
      "JAVIS_DEPLOY_TARGET=hostinger" in HOSTINGER and "DOMAIN_NAME: ${DOMAIN_NAME:-localhost}" in HOSTINGER)
check("compose VPS mặc định được backend nhận là Caddy", "WATCHTOWER_TOKEN" in VPS and "JAVIS_DEPLOY_TARGET: vps" not in VPS)
check("tài liệu mô tả wizard mới", "Lưu & kiểm tra" in DOC and "Sao chép biến" in DOC)

if fails:
    raise SystemExit(f"\nFAIL - test_domain_setup_ui: {len(fails)} lỗi")
print("\nOK - test_domain_setup_ui: tất cả pass")
