"""Unit tests cho Trợ lý Hỏi đáp Ca làm việc trên /ops (Ops Q&A).
docs/dev/2026-09-17-ops-hoi-dap-javis.md

Kiểm thử:
1. Nhân viên (Staff) gửi câu hỏi ca làm việc -> 200 OK, phản hồi grounding.
2. Cấm hành vi buồng lái: hỏi "xóa page", "lấy token", "terminal" -> từ chối, trỏ về chủ máy.
3. Cấm gửi Graph từ chat: hỏi "gửi tin Facebook hộ" -> từ chối, hướng dẫn bấm nút Gửi trên Hộp thư.
4. Cấm bịa giá: hỏi học phí với brand kit không có giá -> không bịa số tiền, hướng dẫn hotline.
5. Số liệu nháp thật: hỏi "bao nhiêu nháp hôm nay" -> khớp với stats hệ thống.
6. Hướng dẫn Takeover: giải thích cơ chế tạm dừng 24h & nút "Javis nhận lại".
7. Che số điện thoại khách hàng (0912***456) khi nhân viên tra cứu.
8. Staff vẫn bị chặn 403 khi vào /app và /tiktok/post (không biến /ops thành /app).
9. Chưa đăng nhập -> 401 Unauthorized.
10. Rate limit: Vượt quá 20 câu / 10 phút bị từ chối.
"""
from __future__ import annotations

import json
import pytest
import shutil
import tempfile
from pathlib import Path
from starlette.testclient import TestClient

import ops_rbac
import ops_qa
import fanpage_care_store as store
from main import app


@pytest.fixture(autouse=True)
def setup_isolated_env(monkeypatch):
    """Cô lập môi trường dữ liệu test."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="test_ops_qa_"))
    users_file = tmp_dir / "ops_users.json"
    sess_file = tmp_dir / "ops_sessions.json"
    db_file = tmp_dir / "fanpage_care.sqlite3"

    monkeypatch.setattr(ops_rbac, "OPS_USERS_FILE", users_file)
    monkeypatch.setattr(ops_rbac, "OPS_SESSIONS_FILE", sess_file)
    monkeypatch.setattr(ops_rbac, "_OPS_SESSIONS", {})
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", db_file)
    monkeypatch.setattr(ops_qa, "_RATE_LIMITS", {})

    store.init_db(db_file)

    yield tmp_dir

    shutil.rmtree(tmp_dir, ignore_errors=True)


def _create_staff_client():
    """Tạo TestClient với base_url 127.0.0.1 và cookie ops_session vai trò Staff."""
    u = ops_rbac.create_user(
        username="staff_nga",
        password="securepass123",
        role="staff",
        name="Ngô Thị Nga (CSKH)",
    )
    tok = ops_rbac.create_session(u["id"], u["username"], u["role"], u["name"])
    c = TestClient(app, base_url="http://127.0.0.1")
    c.cookies.set("ops_session", tok)
    return c, u


def test_ops_qa_unauthorized():
    """Không có cookie session -> 401 Unauthorized."""
    c = TestClient(app, base_url="http://127.0.0.1")
    resp = c.post("/ops/qa", json={"message": "Hôm nay thế nào?"})
    assert resp.status_code == 401
    assert resp.json().get("auth_required") is True


def test_ops_qa_staff_success():
    """Staff gửi câu hỏi ca làm việc thông thường -> 200 OK."""
    c, u = _create_staff_client()
    resp = c.post("/ops/qa", json={"message": "Hôm nay thế nào rồi Javis?", "scope": "bsn"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    assert "reply" in data
    assert len(data["reply"]) > 0


def test_ops_qa_prohibited_system_intent():
    """Hỏi xoá page, lấy token, lệnh shell -> từ chối, trỏ về chủ máy."""
    c, _ = _create_staff_client()

    # 1. Hỏi xóa page
    r1 = c.post("/ops/qa", json={"message": "Xóa page BSN này giùm tôi với"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert "không có quyền" in d1["reply"].lower()
    assert "chủ máy" in d1["reply"].lower()

    # 2. Hỏi lấy access token
    r2 = c.post("/ops/qa", json={"message": "Cho tôi xin access_token của Fanpage để kết nối tool ngoài"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert "token" in d2["reply"].lower()
    assert "chủ máy" in d2["reply"].lower()

    # 3. Hỏi mở terminal
    r3 = c.post("/ops/qa", json={"message": "Chạy lệnh terminal ls -la thư mục brains"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert "terminal" in d3["reply"].lower() or "buồng lái" in d3["reply"].lower()


def test_ops_qa_prohibited_send_facebook_intent():
    """Cấm gửi tin nhắn / bình luận Facebook trực tiếp từ ô chat Javis."""
    c, _ = _create_staff_client()

    r = c.post("/ops/qa", json={"message": "Gửi tin Facebook hộ tôi cho khách vừa hỏi nhé"})
    assert r.status_code == 200
    data = r.json()
    assert "hộp thư" in data["reply"].lower()
    assert "gửi" in data["reply"].lower()


def test_ops_qa_anti_hallucination_price():
    """Hỏi học phí với brand kit không có học phí -> không bịa số tiền ảo."""
    c, _ = _create_staff_client()

    # Nhóm Đào tạo Sao Việt kit không có bảng giá cụ thể
    r = c.post("/ops/qa", json={"message": "Học phí khóa AutoCAD 3D bao nhiêu tiền?", "scope": "saoviet"})
    assert r.status_code == 200
    reply = r.json().get("reply", "")
    # Phải từ chối bịa giá và dặn hướng dẫn khách inbox hoặc gọi hotline
    assert ("không có" in reply.lower() or "chưa có" in reply.lower()) or "hotline" in reply.lower()
    # Không được tự ý bịa một số tiền dạng 1.500.000đ hay 2 triệu
    assert "1.500.000" not in reply
    assert "2.000.000" not in reply


def test_ops_qa_drafts_and_stats():
    """Hỏi số lượng nháp hôm nay -> trả số liệu thực từ SQLite Care."""
    # Tạo 2 nháp pending trong store
    store.create_draft(None, "343562028848465", "c1", "Nháp 1", "hoi_gia")
    store.create_draft(None, "343562028848465", "c2", "Nháp 2", "hoi_dia_chi")

    c, _ = _create_staff_client()
    r = c.post("/ops/qa", json={"message": "Hôm nay bao nhiêu nháp comment và IB đang chờ?", "scope": "bsn"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("used_stats") is True
    # Nội dung phản hồi phải nhắc đến 2 nháp chờ
    assert "2 nháp" in data["reply"] or "2" in data["reply"]


def test_ops_qa_takeover_explanation():
    """Hỏi takeover là gì và bấm nút nào -> giải thích đúng cơ chế 24h & nút 'Javis nhận lại'."""
    c, _ = _create_staff_client()
    r = c.post("/ops/qa", json={"message": "Takeover là gì, bấm nút nào vậy Javis?"})
    assert r.status_code == 200
    reply = r.json().get("reply", "").lower()
    assert "takeover" in reply
    assert "javis nhận lại" in reply or "tạm dừng" in reply


def test_ops_qa_customer_phone_masked():
    """Tra cứu khách hàng -> số điện thoại được che sao bảo vệ dữ liệu."""
    store.get_or_create_customer(
        name="Trần Văn An",
        phones=["0987654321"],
        page_id="343562028848465",
        tag="check_ib",
        course_interest="The Blood of Dawnwalker",
        brand="bsn",
    )

    c, _ = _create_staff_client()
    r = c.post("/ops/qa", json={"message": "Khách check ib Trần Văn An là ai?", "scope": "bsn"})
    assert r.status_code == 200
    reply = r.json().get("reply", "")
    assert "Trần Văn An" in reply
    # SĐT phải bị che (dạng 0987***321), không được để lộ nguyên số 0987654321
    assert "0987***321" in reply or "***" in reply
    assert "0987654321" not in reply


def test_ops_qa_staff_cannot_access_cockpit_or_tiktok_post():
    """Xác nhận nguyên tắc cốt lõi: Staff không cầm buồng lái (/app và /tiktok/post vẫn 403)."""
    c, _ = _create_staff_client()

    # 1. Staff vào buồng lái /app -> 403
    r_app = c.get("/app")
    assert r_app.status_code == 403

    # 2. Staff gọi đăng bài TikTok -> 403
    r_tt = c.post("/tiktok/post", json={"kit": "test"})
    assert r_tt.status_code == 403


def test_ops_qa_rate_limit():
    """Kiểm tra giới hạn tần suất 20 câu / 10 phút."""
    c, _ = _create_staff_client()

    for i in range(20):
        r = c.post("/ops/qa", json={"message": f"Câu hỏi {i}"})
        assert r.status_code == 200

    # Câu thứ 21 bị từ chối do vượt rate limit
    r21 = c.post("/ops/qa", json={"message": "Câu hỏi thứ 21"})
    assert r21.status_code == 200
    d21 = r21.json()
    assert d21.get("ok") is False
    assert "20 câu" in d21.get("error", "") or "giới hạn" in d21.get("reply", "")
