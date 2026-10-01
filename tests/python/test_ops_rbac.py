# ============================================================
# Unit Tests: Javis Ops RBAC Module & Access Control Matrix
# docs/dev/2026-09-16-ops-dashboard-plan.md (Mục 0, 3, 7)
# ============================================================
import json
import pytest
from pathlib import Path
import tempfile
import shutil

from _paths import ROOT, SERVER
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


def test_ops_me_unauthenticated_production_returns_401(monkeypatch):
    """Khi không ở chế độ demo và không có session: GET /ops/me trả về 401."""
    monkeypatch.delenv("JAVIS_OPS_DEMO_AUTO_OWNER", raising=False)
    monkeypatch.delenv("JAVIS_REQUIRE_LOGIN", raising=False)
    from fastapi.testclient import TestClient
    import main
    with TestClient(main.app, base_url="http://127.0.0.1") as client:
        res = client.get("/ops/me")
        assert res.status_code == 401
        data = res.json()
        assert data.get("user") is None
        assert data.get("error") == "unauthorized"


def test_ops_me_demo_auto_owner_when_env_enabled(monkeypatch):
    """Khi bật JAVIS_OPS_DEMO_AUTO_OWNER=1: GET /ops/me tự cấp phiên demo."""
    monkeypatch.setenv("JAVIS_OPS_DEMO_AUTO_OWNER", "1")
    from fastapi.testclient import TestClient
    import main
    with TestClient(main.app, base_url="http://127.0.0.1") as client:
        res = client.get("/ops/me")
        assert res.status_code == 200
        data = res.json()
        assert data.get("user") is not None
        assert data["user"]["role"] == "owner"
        assert data.get("data_source") == "demo_seed"


def test_ops_me_authenticated_owner():
    """Khi có session ops_session hợp lệ: GET /ops/me trả về user tương ứng."""
    tok = ops_rbac.create_session("u_owner", "admin", "owner", "Chủ máy")
    from fastapi.testclient import TestClient
    import main
    with TestClient(main.app, base_url="http://127.0.0.1", cookies={"ops_session": tok}) as client:
        res = client.get("/ops/me")
        assert res.status_code == 200
        data = res.json()
        assert data.get("user") is not None
        assert data["user"]["role"] == "owner"
        assert data.get("data_source") == "real"


def test_multi_role_creation_and_directory():
    """Tạo các tài khoản theo các role chuyên biệt và truy cập danh bạ /ops/directory."""
    roles_to_test = ["cskh", "sales", "warehouse", "marketing", "technical"]
    created = []
    for r in roles_to_test:
        u = ops_rbac.create_user(f"user_{r}", "password123", role=r, name=f"Nhân sự {r.upper()}")
        assert u["role"] == r
        assert u["code"] == ops_rbac.ROLES_REGISTRY[r]["code"]
        assert len(u["permissions"]) > 0
        created.append(u)

    from fastapi.testclient import TestClient
    import main
    tok = ops_rbac.create_session("u_cskh_1", "user_cskh", "cskh", "CSKH Test")
    with TestClient(main.app, base_url="http://127.0.0.1", cookies={"ops_session": tok}) as client:
        res_dir = client.get("/ops/directory")
        assert res_dir.status_code == 200
        users = res_dir.json().get("users", [])
        assert len(users) >= len(roles_to_test)
        usernames = [x["username"] for x in users]
        for r in roles_to_test:
            assert f"user_{r}" in usernames


def test_rbac_matrix_cskh():
    """Chuyên viên CSKH:
    - Được: Duyệt nháp, gửi/bỏ nháp, tiếp quản Messenger, ghi chú CRM, xem đơn hàng, xem danh bạ.
    - CẤM: Unmask SĐT, gộp/xoá CRM, cấu hình bot Care, quét ngay, tạo vận đơn, xem chi phí token, buồng lái.
    """
    cskh = {"id": "u_cskh", "username": "thao_cskh", "role": "cskh"}

    # Được phép:
    for path, method in [
        ("/ops/directory", "GET"),
        ("/ops/inbox", "GET"),
        ("/fanpage-care/drafts/123/send", "POST"),
        ("/fanpage-care/drafts/123/reject", "POST"),
        ("/fanpage-care/handoff", "POST"),
        ("/fanpage-care/customers", "GET"),
        ("/ops/orders", "GET"),
        ("/ops/orders", "POST"),
    ]:
        allowed, reason = ops_rbac.check_access_permission(cskh, path, method)
        assert allowed is True, f"CSKH bị chặn ở {path}: {reason}"

    # Bị cấm:
    for path, method in [
        ("/app", "GET"),
        ("/terminal", "GET"),
        ("/ops/users", "GET"),
        ("/usage/summary", "GET"),
        ("/fanpage-care/customers/merge", "POST"),
        ("/fanpage-care/settings", "POST"),
        ("/fanpage-care/poll-now", "POST"),
        ("/ops/orders/ord_1/create-shipment", "POST"),
        ("/ops/shipping/settings", "POST"),
    ]:
        allowed, reason = ops_rbac.check_access_permission(cskh, path, method)
        assert allowed is False, f"CSKH lẽ ra PHẢI bị chặn ở {path}"


def test_rbac_matrix_warehouse():
    """Nhân viên Kho vận:
    - Được: Xem đơn hàng, tạo vận đơn giao hàng (/create-shipment), xem danh bạ.
    - CẤM: Duyệt nháp Care, huỷ đơn, gộp CRM, sửa bot Care, xem chi phí token, buồng lái.
    """
    kho = {"id": "u_kho", "username": "an_kho", "role": "warehouse"}

    # Được phép:
    for path, method in [
        ("/ops/directory", "GET"),
        ("/ops/orders", "GET"),
        ("/ops/orders/ord_1/create-shipment", "POST"),
        ("/ops/orders/ord_1/confirm", "POST"),
    ]:
        allowed, reason = ops_rbac.check_access_permission(kho, path, method)
        assert allowed is True, f"Warehouse bị chặn ở {path}: {reason}"

    # Bị cấm:
    for path, method in [
        ("/app", "GET"),
        ("/fanpage-care/drafts/123/send", "POST"),
        ("/ops/orders/ord_1/cancel", "POST"),
        ("/fanpage-care/customers/merge", "POST"),
        ("/usage/summary", "GET"),
        ("/ops/users", "GET"),
    ]:
        allowed, reason = ops_rbac.check_access_permission(kho, path, method)
        assert allowed is False, f"Warehouse lẽ ra PHẢI bị chặn ở {path}"


def test_rbac_matrix_marketing():
    """Chuyên viên Marketing & TikTok:
    - Được: Quản lý chiến dịch tiếp thị, xem radar đối thủ, attribution, đăng bài TikTok.
    - CẤM: Đổi loop/kit account TikTok (chỉ owner), tạo vận đơn, quản trị users, buồng lái.
    """
    mkt = {"id": "u_mkt", "username": "lan_mkt", "role": "marketing"}

    # Được phép:
    for path, method in [
        ("/ops/campaigns", "GET"),
        ("/ops/competitor/radar", "GET"),
        ("/ops/attribution/matrix", "GET"),
        ("/tiktok/post", "POST"),
    ]:
        allowed, reason = ops_rbac.check_access_permission(mkt, path, method)
        assert allowed is True, f"Marketing bị chặn ở {path}: {reason}"

    # Bị cấm:
    for path, method in [
        ("/app", "GET"),
        ("/tiktok/loop-toggle", "POST"),
        ("/tiktok/kit-account", "POST"),
        ("/ops/orders/ord_1/create-shipment", "POST"),
        ("/ops/users", "GET"),
        ("/usage/summary", "GET"),
    ]:
        allowed, reason = ops_rbac.check_access_permission(mkt, path, method)
        assert allowed is False, f"Marketing lẽ ra PHẢI bị chặn ở {path}"


def test_rbac_permissions_endpoints(monkeypatch):
    """Kiểm thử API xem danh mục quyền, cấu hình tùy biến và khôi phục mặc định."""
    from fastapi.testclient import TestClient
    import main

    tok_owner = ops_rbac.create_session("u_own", "admin", "owner", "Chủ máy")
    tok_staff = ops_rbac.create_session("u_stf", "nv_01", "staff", "Nhân viên")

    with TestClient(main.app, base_url="http://127.0.0.1") as client:
        # 1. Staff gọi GET /ops/rbac/permissions -> được phép xem
        res_get = client.get("/ops/rbac/permissions", cookies={"ops_session": tok_staff})
        assert res_get.status_code == 200
        data = res_get.json()
        assert "roles" in data
        assert "catalog" in data
        assert "matrix" in data
        assert "default_matrix" in data
        assert len(data["catalog"]) >= 8

        # 2. Staff thử POST thay đổi ma trận -> Bị 403 Forbidden
        res_post_staff = client.post(
            "/ops/rbac/permissions",
            json={"matrix": {"staff": ["*"]}},
            cookies={"ops_session": tok_staff}
        )
        assert res_post_staff.status_code == 403

        # 3. Owner lưu ma trận phân quyền tùy biến
        custom_matrix = {
            "staff": ["care:view", "care:reply", "crm:view", "orders:view"],
            "owner": []  # Cố tình xóa quyền owner để kiểm tra bảo vệ bất biến
        }
        res_save = client.post(
            "/ops/rbac/permissions",
            json={"matrix": custom_matrix},
            cookies={"ops_session": tok_owner}
        )
        assert res_save.status_code == 200
        saved_data = res_save.json()
        assert saved_data["ok"] is True
        # Bất biến: Owner luôn luôn giữ [*]
        assert saved_data["matrix"]["owner"] == ["*"]
        assert "care:view" in saved_data["matrix"]["staff"]

        # 4. Owner khôi phục về mặc định
        res_reset = client.post(
            "/ops/rbac/permissions/reset",
            cookies={"ops_session": tok_owner}
        )
        assert res_reset.status_code == 200
        reset_data = res_reset.json()
        assert reset_data["ok"] is True
        assert reset_data["matrix"]["owner"] == ["*"]


