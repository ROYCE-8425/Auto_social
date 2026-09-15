import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import config
import fanpage_care
import fanpage_care_graph
import fanpage_care_store as store


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        vault_dir = p / "vault"
        vault_dir.mkdir(parents=True)
        kits_dir = vault_dir / "wiki" / "brand-kits"
        kits_dir.mkdir(parents=True)

        q7_kit = kits_dir / "trung-tam-tin-hoc-sao-viet-quan-7.md"
        q7_kit.write_text(
            """# Trung Tâm Tin Học Sao Việt Quận 7
- Page ID: 108426965133947
- Tên Fanpage: Trung Tâm Tin Học Sao Việt Quận 7
- Cơ sở / địa chỉ: Florita, Quận 7
- Hotline: 0935 195 118
""",
            encoding="utf-8",
        )

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(store, "DEFAULT_DB_PATH", state_dir / "fanpage_care.sqlite3")
        monkeypatch.setattr(fanpage_care_graph, "STATE_DIR", state_dir)

        yield td


@pytest.mark.anyio
async def test_lead_creates_kanban_task_suggest_only(monkeypatch):
    """Bình luận lead phải tạo Kanban task suggest mode, cấm auto/full."""
    fake_tasks_feature = MagicMock()
    fake_tasks_feature.enqueue.return_value = "task-123"

    mock_settings = {
        "fanpage_care": {
            "enabled": True,
            "mode": "suggest",
            "brain": "Brain Default",
            "pages_per_tick": 10,
            "max_events_per_tick": 100,
        }
    }
    monkeypatch.setattr(config, "read_settings", lambda: mock_settings)

    fake_items = [
        {
            "comment_id": "comment_lead_999",
            "from_id": "user_lead",
            "from_name": "Nguyễn Văn Lead",
            "message": "Tôi muốn học Excel tối 2-4-6, gọi lại số 0912345678 giúp mình",
            "post_id": "post_1",
            "created_time": 1700000000,
        }
    ]

    async def mock_graph_call(tool, args=None, *a, **k):
        if tool == "fb_page_inbox_comments":
            return json.dumps({"items": fake_items})
        return json.dumps({"ok": True})

    monkeypatch.setattr(fanpage_care_graph, "call", mock_graph_call)

    deps = fanpage_care.FanpageCareDeps(
        brain="Brain Default",
        vault_root=Path(config.STATE_DIR).parent / "vault",
        tasks_feature=fake_tasks_feature,
    )
    feature = fanpage_care.FanpageCareFeature(deps)

    res = await feature.poll_tick()
    assert res["status"] == "ok"
    assert res["events_ingested"] == 1

    # Kiểm tra tasks_feature.enqueue được gọi
    assert fake_tasks_feature.enqueue.called
    kwargs = fake_tasks_feature.enqueue.call_args.kwargs
    assert kwargs["execution_mode"] == "suggest"  # Bắt buộc suggest, cấm auto/full
    assert kwargs["capability"] == "mcp-read"
    assert kwargs["created_by"] == "fanpage_care"
    assert kwargs["idempotency_key"] == "care:comment_lead_999"
    assert kwargs["brain"] == "Brain Default"
    assert kwargs["priority"] == 1  # Có SĐT -> priority 1
    assert "0912345678" in kwargs["title"] or "0912345678" in kwargs["intent"]


@pytest.mark.anyio
async def test_send_daily_digest_to_inbox(monkeypatch):
    """Gửi digest 20h vào hòm thư inbox."""
    fake_inbox_add = MagicMock()

    # Thêm một vài sự kiện vào store để có stats
    store.init_db()
    store.record_event({"kind": "comment", "object_id": "c_1", "page_id": "108426965133947", "body": "Test", "class": "lead"})
    store.record_event({"kind": "comment", "object_id": "c_2", "page_id": "108426965133947", "body": "Test 2", "class": "faq"})
    store.record_action(1, "reply", "c_1", "template", "care")
    store.record_action(2, "hide", "c_spam", "spam", "care")
    store.create_draft(1, "108426965133947", "c_1", "Nháp", "faq")

    deps = fanpage_care.FanpageCareDeps(
        brain="Brain Default",
        vault_root=Path(config.STATE_DIR).parent / "vault",
        inbox_add=fake_inbox_add,
    )
    feature = fanpage_care.FanpageCareFeature(deps)

    await feature.send_daily_digest()

    assert fake_inbox_add.called
    kwargs = fake_inbox_add.call_args.kwargs
    assert kwargs["kind"] == "report"
    assert kwargs["source"] == "fanpage_care"
    assert kwargs["brain"] == "Brain Default"
    assert kwargs["read"] is False

    msg_body = fake_inbox_add.call_args.args[0]
    assert "Báo cáo Chăm sóc Fanpage" in msg_body
    assert "bình luận mới" in msg_body
    assert "lead (có SĐT)" in msg_body
    assert "spam đã ẩn" in msg_body
    assert "draft chờ duyệt" in msg_body
