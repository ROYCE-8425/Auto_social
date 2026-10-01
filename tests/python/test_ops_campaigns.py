# -*- coding: utf-8 -*-
import json
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from _paths import ROOT, SERVER
import config
import ops_campaign
import ops_campaign_store
import task_store
from main import app


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Thiết lập môi trường biệt lập với SQLite tạm cho Campaigns và Kanban."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)

        campaign_db = state_dir / "test_ops_campaigns.sqlite3"
        kanban_db = state_dir / "kanban.sqlite3"

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(ops_campaign_store, "DEFAULT_DB_PATH", campaign_db)

        # Khởi tạo TaskStore và OpsCampaignStore
        t_store = task_store.TaskStore(kanban_db)
        t_store.ensure_board(str(state_dir))
        ops_campaign_store.init_db(campaign_db)

        # Mock authentication cho ops user trong TestClient
        import ops_rbac
        monkeypatch.setattr(
            ops_rbac,
            "get_current_ops_user",
            lambda request: {"username": "admin_test", "role": "owner", "display_name": "Admin Test"},
        )

        yield {
            "state_dir": state_dir,
            "campaign_db": campaign_db,
            "kanban_db": kanban_db,
            "task_store": t_store,
        }


def test_create_campaign_persists_to_db():
    """a) Tạo campaign persist được vào SQLite ops_campaigns và ops_campaign_items."""
    res = ops_campaign.create_autopilot_campaign(
        goal="Tăng trưởng doanh số khóa học MOS cho 100 học viên",
        target_metric="100 học viên",
        duration_weeks=4,
        budget_vnd=15000000,
        platforms=["tiktok", "facebook"],
    )

    assert res["ok"] is True
    assert "campaign_id" in res
    cid = res["campaign_id"]
    assert cid.startswith("camp_")

    # Kiểm tra persist trực tiếp từ database
    saved = ops_campaign_store.get_campaign(cid)
    assert saved is not None
    assert saved["id"] == cid
    assert saved["goal"] == "Tăng trưởng doanh số khóa học MOS cho 100 học viên"
    assert saved["target_metric"] == "100 học viên"
    assert saved["duration_weeks"] == 4
    assert saved["budget_vnd"] == 15000000
    assert saved["status"] == "active"
    assert "tiktok" in saved["platforms"]
    assert "facebook" in saved["platforms"]


def test_create_campaign_generates_kanban_task_ids():
    """b) Tạo campaign sinh task ids thật trong Kanban store và gắn vào campaign."""
    res = ops_campaign.create_autopilot_campaign(
        goal="Chiến dịch tuyển sinh cấp tốc mùa thi",
        target_metric="30 học viên",
        duration_weeks=2,
        budget_vnd=8000000,
        platforms=["facebook"],
    )

    assert res["ok"] is True
    task_ids = res.get("task_ids")
    assert isinstance(task_ids, list)
    assert len(task_ids) == 4  # 4 tasks: review, content, publishing, follow-up

    for tid in task_ids:
        assert isinstance(tid, str)
        assert tid.startswith("t_")

    # Kiểm tra tasks đã thực sự tồn tại trong kanban store
    kanban_db = config.STATE_DIR / "kanban.sqlite3"
    t_store = task_store.TaskStore(kanban_db)
    for tid in task_ids:
        task = t_store.get_task(tid)
        assert task is not None
        assert "Chiến dịch tuyển sinh" in task["title"]
        assert task["created_by"] == "campaign_autopilot"


def test_get_campaign_returns_correct_items():
    """c) API GET /ops/campaigns/{id} trả đúng các items và tổng hợp đầy đủ."""
    client = TestClient(app, base_url="http://127.0.0.1")

    # 1. Tạo chiến dịch qua POST API
    post_res = client.post(
        "/ops/campaigns/autopilot",
        json={
            "goal": "Ra mắt dịch vụ thiết kế landing page chuyên nghiệp",
            "target_metric": "20 khách hàng doanh nghiệp",
            "duration_weeks": 3,
            "budget_vnd": 12000000,
            "platforms": ["tiktok", "facebook"],
        },
    )
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["ok"] is True
    cid = data["campaign_id"]
    task_ids = data["task_ids"]

    # 2. Gọi GET /ops/campaigns/{id}
    get_res = client.get(f"/ops/campaigns/{cid}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["ok"] is True
    assert detail["campaign"]["id"] == cid
    assert detail["campaign"]["goal"] == "Ra mắt dịch vụ thiết kế landing page chuyên nghiệp"

    # Kiểm tra items: 3 tuần * 3 bài/tuần = 9 bài
    items = detail["items"]
    assert len(items) == 9
    for it in items:
        assert it["campaign_id"] == cid
        assert it["platform"] in ["tiktok", "facebook"]
        assert it["status"] == "draft"  # Mặc định là draft khi chưa có post_id thật
        assert it["external_post_id"] == ""  # Không có post_id thật thì rỗng

    # 3. Gọi GET /ops/campaigns để kiểm tra danh sách
    list_res = client.get("/ops/campaigns")
    assert list_res.status_code == 200
    c_list = list_res.json()
    assert c_list["ok"] is True
    assert len(c_list["campaigns"]) >= 1
    found = next((c for c in c_list["campaigns"] if c["id"] == cid), None)
    assert found is not None
    assert found["total_items"] == 9


def test_validation_rejects_invalid_inputs():
    """Kiểm tra các trường hợp input không hợp lệ bị từ chối 400."""
    client = TestClient(app, base_url="http://127.0.0.1")

    # 1. Goal rỗng
    r1 = client.post("/ops/campaigns/autopilot", json={"goal": "  "})
    assert r1.status_code == 400
    assert "goal" in r1.json()["error"].lower()

    # 2. Duration âm hoặc bằng 0
    r2 = client.post("/ops/campaigns/autopilot", json={"goal": "Hợp lệ", "duration_weeks": 0})
    assert r2.status_code == 400

    # 3. Ngân sách âm
    r3 = client.post("/ops/campaigns/autopilot", json={"goal": "Hợp lệ", "budget_vnd": -5000})
    assert r3.status_code == 400

    # 4. Platforms rỗng
    r4 = client.post("/ops/campaigns/autopilot", json={"goal": "Hợp lệ", "platforms": []})
    assert r4.status_code == 400


def test_kanban_failure_returns_error_and_does_not_persist(monkeypatch):
    """d) Nếu Kanban enqueue fail, trả lỗi rõ ràng và không lưu campaign rác."""
    client = TestClient(app, base_url="http://127.0.0.1")

    # Giả lập Kanban store gặp lỗi khi enqueue
    def mock_fail_enqueue(*args, **kwargs):
        raise RuntimeError("Kanban SQLite connection is locked")

    monkeypatch.setattr(task_store.TaskStore, "enqueue", mock_fail_enqueue)

    res = client.post(
        "/ops/campaigns/autopilot",
        json={"goal": "Chiến dịch thử nghiệm thất bại"},
    )
    assert res.status_code == 500
    err = res.json()["error"]
    assert "Kanban" in err or "locked" in err

    # Đảm bảo không lưu campaign rác trong SQLite
    campaigns = ops_campaign_store.list_campaigns()
    assert not any("Chiến dịch thử nghiệm thất bại" in c["goal"] for c in campaigns)
