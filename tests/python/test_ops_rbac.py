# ============================================================
# Unit Tests: Javis Ops RBAC Module & Access Control Matrix
# docs/dev/2026-09-16-ops-dashboard-plan.md (Mục 0, 3, 7)
# ============================================================
import json
import pytest
from pathlib import Path
import tempfile
import shutil

import ops_rbac


@pytest.fixture(autouse=True)
def setup_temp_ops_dir(monkeypatch):
    """Cô lập thư mục STATE_DIR để test không ảnh hưởng tới dữ liệu chạy thật."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="test_ops_rbac_"))
    users_file = tmp_dir / "ops_users.json"
    sess_file = tmp_dir / "ops_sessions.json"

    monkeypatch.setattr(ops_rbac, "OPS_USERS_FILE", users_file)
    monkeypatch.setattr(ops_rbac, "OPS_SESSIONS_FILE", sess_file)
    monkeypatch.setattr(ops_rbac, "_OPS_SESSIONS", {})

    yield tmp_dir

    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_password_hashing():
    """Băm và xác minh mật khẩu bằng PBKDF2-HMAC-SHA256."""
    h, salt = ops_rbac.hash_ops_password("MatKhau123!")
    assert h and salt
    assert ops_rbac.verify_ops_password("MatKhau123!", h, salt)
    assert not ops_rbac.verify_ops_password("SaiPass!", h, salt)


def test_user_crud():
    """Tạo, đọc, sửa, xoá tài khoản nhân sự."""
    u1 = ops_rbac.create_user(
        username="staff_lan",
        password="password123",
        role="staff",
        name="Nguyễn Thị Lan (CSKH)",
    )
    assert u1["username"] == "staff_lan"
    assert u1["role"] == "staff"
    assert "password_hash" not in u1  # Đã sanitize

    # Trùng username bị từ chối
    with pytest.raises(ValueError, match="đã tồn tại"):
        ops_rbac.create_user("staff_lan", "anotherpass123")

    # Mật khẩu quá ngắn (<6 ký tự)
    with pytest.raises(ValueError, match="tối thiểu 6 ký tự"):
        ops_rbac.create_user("staff_tuan", "123")

    # Role không hợp lệ
    with pytest.raises(ValueError, match="Role không hợp lệ"):
        ops_rbac.create_user("staff_bad", "password123", role="superadmin")

    # Tìm kiếm
    found = ops_rbac.get_user_by_username("STAFF_LAN")  # Case insensitive
    assert found is not None
    assert found["id"] == u1["id"]

    # Cập nhật role
    updated = ops_rbac.update_user(u1["id"], {"role": "manager", "name": "Nguyễn Thị Lan (Trưởng nhóm)"})
    assert updated is not None
    assert updated["role"] == "manager"
    assert updated["name"] == "Nguyễn Thị Lan (Trưởng nhóm)"

    # Xoá
    deleted = ops_rbac.delete_user(u1["id"])
    assert deleted is True
    assert ops_rbac.get_user_by_id(u1["id"]) is None


def test_session_lifecycle():
    """Tạo phiên, đọc phiên và huỷ phiên."""
    tok = ops_rbac.create_session("u_123", "mai_cskh", "staff", "Mai")
    assert tok.startswith("ops_")

    s = ops_rbac.get_session(tok)
    assert s is not None
    assert s["username"] == "mai_cskh"
    assert s["role"] == "staff"

    ops_rbac.drop_session(tok)
    assert ops_rbac.get_session(tok) is None


def test_rbac_matrix_owner():
    """Chủ máy (Owner) có toàn quyền trên mọi route."""
    owner = {"id": "owner", "username": "admin", "role": "owner"}
    for path, method in [
        ("/", "GET"),
        ("/terminal", "GET"),
        ("/mcp/install", "POST"),
        ("/settings", "POST"),
        ("/fanpage-care/settings", "POST"),
        ("/fanpage-care/customers/merge", "POST"),
        ("/ops/users", "GET"),
    ]:
        allowed, reason = ops_rbac.check_access_permission(owner, path, method)
        assert allowed is True, f"Owner bị chặn ở {path}: {reason}"


def test_rbac_matrix_staff():
    """Nhân viên CSKH (staff):
    - Được: xem/gửi/bỏ nháp, xem khách, tạo việc, Messenger, xem /ops.
    - CẤM: console chủ máy (/), terminal, MCP, gộp CRM, xoá CRM, cấu hình Care, Quét ngay, xem tiền token.
    """
    staff = {"id": "u_1", "username": "staff_1", "role": "staff"}

    # Các quyền ĐƯỢC PHÉP của Staff:
    allowed_routes = [
        ("/", "GET"),
        ("/chao", "GET"),
        ("/ops", "GET"),
        ("/ops/inbox", "GET"),
        ("/ops/customers", "GET"),
        ("/ops/tasks", "GET"),
        ("/fanpage-care/state", "GET"),
        ("/fanpage-care/inbox", "GET"),
        ("/fanpage-care/drafts/123_456/send", "POST"),
        ("/fanpage-care/drafts/123_456/reject", "POST"),
        ("/fanpage-care/handoff", "POST"),
        ("/fanpage-care/customers", "GET"),
        ("/fanpage-care/customers/c_1", "GET"),
        ("/fanpage-care/conversations", "GET"),
        ("/fanpage-care/conversations/release-takeover", "POST"),
        ("/kanban", "GET"),
        ("/inbox", "GET"),
    ]
    for path, method in allowed_routes:
        allowed, reason = ops_rbac.check_access_permission(staff, path, method)
        assert allowed is True, f"Staff lẽ ra được phép ở {path}, nhưng bị chặn: {reason}"

    # Các hành vi CẤM TUYỆT ĐỐI của Staff (403):
    forbidden_routes = [
        ("/app", "GET"),                  # Console chủ máy
        ("/index.html", "GET"),           # Console chủ máy
        ("/terminal", "GET"),             # Terminal máy chủ
        ("/mcp/tools", "GET"),            # MCP
        ("/settings", "POST"),            # Settings Javis
        ("/chat", "POST"),                # Chat trực tiếp với não Javis
        ("/usage/summary", "GET"),        # Chi phí token (chỉ quản lý)
        ("/fanpage-care/customers/merge", "POST"),  # Gộp CRM (chỉ quản lý)
        ("/fanpage-care/customers/c_1", "DELETE"),  # Xoá CRM (chỉ quản lý)
        ("/fanpage-care/settings", "POST"),         # Sửa settings Care
        ("/fanpage-care/poll-now", "POST"),         # Quét ngay
        ("/ops/users", "GET"),                      # Quản lý tài khoản (chỉ chủ máy)
        ("/kanban/run", "POST"),                    # Kích hoạt việc tự động
    ]
    for path, method in forbidden_routes:
        allowed, reason = ops_rbac.check_access_permission(staff, path, method)
        assert allowed is False, f"Staff lẽ ra PHẢI bị chặn ở {path}, nhưng lại lọt!"


def test_rbac_matrix_manager():
    """Quản lý (manager):
    - Được: toàn bộ của staff + gộp/xoá CRM, cấu hình Care (trừ mode full), Quét ngay, xem chi phí token.
    - CẤM: console chủ máy (/), terminal, MCP, chat não, mode full, bật tắt kill switch, quản lý tài khoản (/ops/users).
    """
    manager = {"id": "u_2", "username": "manager_1", "role": "manager"}

    # Các quyền ĐƯỢC PHÉP của Manager:
    allowed_routes = [
        ("/", "GET"),
        ("/chao", "GET"),
        ("/ops", "GET"),
        ("/fanpage-care/customers/merge", "POST"),
        ("/fanpage-care/customers/c_1", "DELETE"),
        ("/fanpage-care/poll-now", "POST"),
        ("/usage/summary", "GET"),
        ("/fanpage-care/settings", "POST"),  # payload thông thường (chưa mode=full)
    ]
    for path, method in allowed_routes:
        allowed, reason = ops_rbac.check_access_permission(manager, path, method)
        assert allowed is True, f"Manager lẽ ra được phép ở {path}, nhưng bị chặn: {reason}"

    # CẤM Manager bật mode=full hoặc kill_switch (chỉ chủ máy):
    allowed_full, _ = ops_rbac.check_access_permission(
        manager, "/fanpage-care/settings", "POST", payload={"mode": "full"}
    )
    assert allowed_full is False, "Manager CẤM bật mode=full"

    allowed_kill, _ = ops_rbac.check_access_permission(
        manager, "/fanpage-care/settings", "POST", payload={"kill_switch": True}
    )
    assert allowed_kill is False, "Manager CẤM can thiệp Kill Switch"

    # CẤM Manager buồng lái và tài khoản chủ:
    forbidden_routes = [
        ("/app", "GET"),
        ("/terminal", "GET"),
        ("/mcp", "GET"),
        ("/chat", "POST"),
        ("/ops/users", "GET"),
        ("/kanban/run", "POST"),
    ]
    for path, method in forbidden_routes:
        allowed, reason = ops_rbac.check_access_permission(manager, path, method)
        assert allowed is False, f"Manager lẽ ra PHẢI bị chặn ở {path}, nhưng lại lọt!"
