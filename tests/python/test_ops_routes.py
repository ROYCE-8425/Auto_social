# ============================================================
# Integration Tests: Javis Ops HTTP Routes & 403 Guards
# docs/dev/2026-09-16-ops-dashboard-plan.md
# ============================================================
import pytest
from fastapi.testclient import TestClient
import tempfile
import shutil
from pathlib import Path

# Set up test environment
import main
import ops_rbac
import config as cfgmod


@pytest.fixture
def client(monkeypatch):
    tmp_dir = Path(tempfile.mkdtemp(prefix="test_ops_routes_"))
    users_file = tmp_dir / "ops_users.json"
    sess_file = tmp_dir / "ops_sessions.json"

    monkeypatch.setattr(ops_rbac, "OPS_USERS_FILE", users_file)
    monkeypatch.setattr(ops_rbac, "OPS_SESSIONS_FILE", sess_file)
    monkeypatch.setattr(ops_rbac, "_OPS_SESSIONS", {})

    with TestClient(main.app, base_url="http://127.0.0.1") as c:
        yield c, tmp_dir

    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_ops_page_served(client):
    """Truy cập /ops trả về trang HTML5 SPA."""
    c, _ = client
    resp = c.get("/ops")
    assert resp.status_code == 200
    assert "Javis Ops" in resp.text or "<div id=\"root\">" in resp.text


def test_ops_login_and_logout(client):
    """Tạo user staff, đăng nhập qua /ops/auth/login, lấy /ops/me, rồi logout."""
    c, _ = client

    # Tạo staff
    ops_rbac.create_user("staff_nga", "securepass123", role="staff", name="Nga")

    # Đăng nhập sai pass
    res_fail = c.post("/ops/auth/login", json={"username": "staff_nga", "password": "wrong"})
    assert res_fail.status_code == 401

    # Đăng nhập đúng
    res_ok = c.post("/ops/auth/login", json={"username": "staff_nga", "password": "securepass123"})
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert data["ok"] is True
    assert data["user"]["username"] == "staff_nga"
    assert data["user"]["role"] == "staff"

    # Gán cookies cho client
    c.cookies.set("ops_session", res_ok.cookies.get("ops_session"))

    # /ops/me trả thông tin staff
    res_me = c.get("/ops/me")
    assert res_me.status_code == 200
    assert res_me.json()["user"]["username"] == "staff_nga"

    # Staff được xem landing `/`; cấm buồng lái `/app`
    res_landing = c.get("/")
    assert res_landing.status_code == 200
    assert "SÈO TRUM" in res_landing.text or "Javis Ops" in res_landing.text
    res_console = c.get("/app")
    assert res_console.status_code == 403
    assert "Chỉ chủ máy mới được truy cập console điều khiển" in res_console.text

    # Staff cố tình gọi /ops/users -> BỊ CHẶN 403
    res_users = c.get("/ops/users")
    assert res_users.status_code == 403

    # Staff cố tình gọi /fanpage-care/poll-now -> BỊ CHẶN 403
    res_poll = c.post("/fanpage-care/poll-now")
    assert res_poll.status_code == 403

    # Staff cố tình gọi /fanpage-care/customers/merge -> BỊ CHẶN 403
    res_merge = c.post("/fanpage-care/customers/merge", json={"source_id": "c1", "target_id": "c2"})
    assert res_merge.status_code == 403

    # Logout
    res_out = c.post("/ops/auth/logout")
    assert res_out.status_code == 200


def test_manager_permissions(client):
    """Manager được phép gộp CRM, poll-now, nhưng bị chặn mode=full và /ops/users."""
    c, _ = client

    ops_rbac.create_user("mgr_thang", "managerpass123", role="manager", name="Thắng")
    res_ok = c.post("/ops/auth/login", json={"username": "mgr_thang", "password": "managerpass123"})
    assert res_ok.status_code == 200
    c.cookies.set("ops_session", res_ok.cookies.get("ops_session"))

    # Manager vào /ops/users -> 403 (chỉ owner)
    res_users = c.get("/ops/users")
    assert res_users.status_code == 403

    # Manager cố tình mở buồng lái /app -> 403
    res_cockpit = c.get("/app")
    assert res_cockpit.status_code == 403

    # Manager cố bật mode=full -> 403
    res_full = c.post("/fanpage-care/settings", json={"mode": "full"})
    assert res_full.status_code == 403


def test_owner_user_management(client, monkeypatch):
    """Owner qua cookie javis_session quản lý được tài khoản /ops/users."""
    c, _ = client

    # Giả lập phiên admin chủ máy hợp lệ
    monkeypatch.setattr(cfgmod, "valid_session", lambda tok: tok == "valid_admin_tok")
    c.cookies.set("javis_session", "valid_admin_tok")

    # Owner xem /ops/me -> role owner
    res_me = c.get("/ops/me")
    assert res_me.status_code == 200
    assert res_me.json()["user"]["role"] == "owner"

    # Owner lấy danh sách users
    res_list = c.get("/ops/users")
    assert res_list.status_code == 200

    # Owner tạo user mới
    res_create = c.post("/ops/users", json={
        "username": "staff_hoa",
        "password": "pass_for_hoa",
        "role": "staff",
        "name": "Hoa CSKH",
    })
    assert res_create.status_code == 200
    assert res_create.json()["ok"] is True
    user_id = res_create.json()["user"]["id"]

    # Owner xoá user
    res_del = c.delete(f"/ops/users/{user_id}")
    assert res_del.status_code == 200
    assert res_del.json()["ok"] is True
