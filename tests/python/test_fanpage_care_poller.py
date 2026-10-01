"""Test suite cho poller trong server/fanpage_care.py."""
import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from _paths import ROOT, SERVER
import config
import fanpage_care
import fanpage_care_graph
import fanpage_care_store as store
import ops_automation_engine
import ops_order_store


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
        monkeypatch.setattr(ops_order_store, "DEFAULT_DB_PATH", state_dir / "ops_orders.sqlite3")
        monkeypatch.setattr(ops_automation_engine, "KILL_SWITCH_FILE", state_dir / "ops_automation_kill_switch.json")
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


@pytest.mark.anyio
async def test_messenger_sales_automation_price_reply(setup_env, monkeypatch):
    vault = setup_env["vault"]
    page_id = "108426965133947"
    monkeypatch.setattr(
        config,
        "read_settings",
        lambda: {
            "fanpage_care": {
                "enabled": True,
                "mode": "auto",
                "kill_switch": False,
                "quiet_hours": "00-00",
                "features": {"auto_reply_messenger": True},
            }
        },
    )

    ops_order_store.init_db()
    ops_automation_engine.set_kill_switch(False)
    product = ops_order_store.create_product({
        "sku": "SKU-MOUSE-SILENT",
        "name": "Chuột Không Dây Silent Pro",
        "price": 250000,
        "sale_price": 220000,
        "stock": 12,
    })
    ops_order_store.add_product_alias(product["id"], "chuột silent")
    ops_order_store.bind_product_to_page(product["id"], page_id=page_id, channel="messenger")

    sent_messages = []

    async def mock_graph_call(tool, args=None, *a, **k):
        if tool == "fb_message_send":
            sent_messages.append(args)
            return json.dumps({"recipient_id": args["recipient_id"], "message_id": "mid_sales_1"})
        return json.dumps({"ok": True})

    monkeypatch.setattr(fanpage_care_graph, "call", mock_graph_call)

    deps = fanpage_care.FanpageCareDeps(vault_root=vault)
    feat = fanpage_care.FanpageCareFeature(deps)
    msg = {
        "sender": {"id": "psid_sales_1", "name": "Anh Test"},
        "recipient": {"id": page_id},
        "timestamp": int(time.time() * 1000),
        "message": {"mid": "m_sales_price_1", "text": "Chuột silent giá bao nhiêu shop?"},
    }

    res = await feat.process_inbound_message(page_id, msg)

    assert res["replied"] is True
    assert sent_messages
    assert sent_messages[0]["recipient_id"] == "psid_sales_1"
    assert "220" in sent_messages[0]["message"] or "250" in sent_messages[0]["message"]
    outbox = ops_order_store.list_outbox_messages(status="sent")
    assert len(outbox) == 1
    assert outbox[0]["thread_id"] == "psid_sales_1"
