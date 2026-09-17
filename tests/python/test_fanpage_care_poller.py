"""Test suite cho poller trong server/fanpage_care.py."""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

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

        # Tạo brand kit mẫu
        q7_kit = kits_dir / "trung-tam-tin-hoc-sao-viet-quan-7.md"
        q7_kit.write_text(
            """# Trung Tâm Tin Học Sao Việt Quận 7
- Page ID: 108426965133947
- Tên Fanpage: Trung Tâm Tin Học Sao Việt Quận 7
- Cơ sở / địa chỉ: Phòng A1-02.04 Florita, Lô A1, KDC Him Lam, Tân Hưng, Quận 7, TP.HCM
- Hotline / Zalo: 0935 195 118
- Page test: true
""",
            encoding="utf-8",
        )

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(store, "DEFAULT_DB_PATH", state_dir / "fanpage_care.sqlite3")
        monkeypatch.setattr(fanpage_care_graph, "STATE_DIR", state_dir)
        monkeypatch.setattr(fanpage_care_graph, "_CARE_AUDIT_PATH", state_dir / "fanpage_care_audit.jsonl")
        monkeypatch.setattr(fanpage_care_graph, "_MCP_AUDIT_PATH", state_dir / "mcp_audit.jsonl")

        yield {"state": state_dir, "vault": vault_dir}


@pytest.mark.anyio
async def test_poller_single_flight(setup_env):
    vault = setup_env["vault"]
    deps = fanpage_care.FanpageCareDeps(vault_root=vault)
    feat = fanpage_care.FanpageCareFeature(deps)

    feat._tick_running = True
    res = await feat.poll_tick()
    assert res["status"] == "skipped"
    assert res["reason"] == "already_running"


@pytest.mark.anyio
async def test_poller_disabled(setup_env, monkeypatch):
    vault = setup_env["vault"]
    monkeypatch.setattr(config, "read_settings", lambda: {"fanpage_care": {"enabled": False}})
    deps = fanpage_care.FanpageCareDeps(vault_root=vault)
    feat = fanpage_care.FanpageCareFeature(deps)

    res = await feat.poll_tick()
    assert res["status"] == "skipped"
    assert res["reason"] == "disabled"


@pytest.mark.anyio
async def test_poller_ingest_suggest_mode(setup_env, monkeypatch):
    vault = setup_env["vault"]
    monkeypatch.setattr(
        config,
        "read_settings",
        lambda: {"fanpage_care": {"enabled": True, "mode": "suggest", "kill_switch": False}},
    )

    fake_items = [
        {
            "comment_id": "c_faq_1",
            "from_id": "user_1",
            "from_name": "Nguyễn Văn A",
            "message": "Cho em hỏi học phí bên mình với ạ",
            "post_id": "post_1",
            "created_time": 1700000000,
        },
        {
            "comment_id": "c_lead_1",
            "from_id": "user_2",
            "from_name": "Trần Thị B",
            "message": "Tư vấn khóa excel giúp em qua sđt 0901234567",
            "post_id": "post_1",
            "created_time": 1700000010,
        },
        {
            "comment_id": "c_own_1",
            "from_id": "108426965133947",  # Comment của Page
            "from_name": "Page Admin",
            "message": "Cảm ơn các bạn",
            "post_id": "post_1",
            "created_time": 1700000020,
        },
    ]

    async def mock_graph_call(tool, args=None, *a, **k):
        if tool == "fb_page_inbox_comments":
            return json.dumps({"items": fake_items})
        return json.dumps({"ok": True})

    monkeypatch.setattr(fanpage_care_graph, "call", mock_graph_call)

    mock_tasks = MagicMock()
    deps = fanpage_care.FanpageCareDeps(vault_root=vault, tasks_feature=mock_tasks)
    feat = fanpage_care.FanpageCareFeature(deps)

    res = await feat.poll_tick()
    assert res["status"] == "ok"
    assert res["events_ingested"] == 2  # c_own_1 bị bỏ qua
    assert res["replies_sent"] == 0     # Mode suggest không gửi Graph
    assert res["drafts_created"] >= 2   # Tạo draft cho FAQ và Lead

    # Kiểm tra SQLite events
    events = store.list_events()
    assert len(events) == 2
    assert {e["object_id"] for e in events} == {"c_faq_1", "c_lead_1"}

    # Kiểm tra CRM markdown
    cust_files = list((vault / "crm" / "customers").glob("*.md"))
    assert len(cust_files) == 2


@pytest.mark.anyio
async def test_poller_auto_mode(setup_env, monkeypatch):
    vault = setup_env["vault"]
    monkeypatch.setattr(
        config,
        "read_settings",
        lambda: {
            "fanpage_care": {
                "enabled": True,
                "mode": "auto",
                "kill_switch": False,
                "quiet_hours": "00-00",
                "features": {"auto_reply_comments": True},
            }
        },
    )

    fake_items = [
        {
            "comment_id": "c_faq_2",
            "from_id": "user_3",
            "from_name": "Lê C",
            "message": "Trung tâm ở địa chỉ nào vậy ạ?",
            "post_id": "post_1",
            "created_time": 1700000030,
        },
    ]

    replies = []

    async def mock_graph_call(tool, args=None, *a, **k):
        if tool == "fb_page_inbox_comments":
            return json.dumps({"items": fake_items})
        if tool == "fb_page_reply":
            replies.append(args)
            return json.dumps({"id": "fb_reply_1"})
        return json.dumps({"ok": True})

    monkeypatch.setattr(fanpage_care_graph, "call", mock_graph_call)

    deps = fanpage_care.FanpageCareDeps(vault_root=vault)
    feat = fanpage_care.FanpageCareFeature(deps)

    res = await feat.poll_tick()
    assert res["status"] == "ok"
    assert res["events_ingested"] == 1
    assert res["replies_sent"] == 1
    assert len(replies) == 1
    assert "Florita" in replies[0]["message"]
    assert replies[0]["comment_id"] == "c_faq_2"
