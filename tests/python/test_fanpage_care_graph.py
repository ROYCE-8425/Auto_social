"""Test suite cho server/fanpage_care_graph.py."""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import config
import fanpage_care_graph


@pytest.fixture(autouse=True)
def temp_state(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        monkeypatch.setattr(config, "STATE_DIR", p)
        monkeypatch.setattr(fanpage_care_graph, "STATE_DIR", p)
        monkeypatch.setattr(fanpage_care_graph, "_MCP_AUDIT_PATH", p / "mcp_audit.jsonl")
        monkeypatch.setattr(fanpage_care_graph, "_CARE_AUDIT_PATH", p / "fanpage_care_audit.jsonl")
        yield p


@pytest.mark.anyio
async def test_graph_call_when_care_disabled(monkeypatch):
    monkeypatch.setattr(config, "read_settings", lambda: {"fanpage_care": {"enabled": False}})
    res = await fanpage_care_graph.call("fb_page_reply", {"comment_id": "123", "message": "test"})
    assert res.startswith("ERROR: fanpage_care_disabled")

    # Kiểm tra audit log
    audit_file = fanpage_care_graph._CARE_AUDIT_PATH
    assert audit_file.exists()
    lines = audit_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["err"] == "fanpage_care_disabled"
    assert rec["ok"] is False


@pytest.mark.anyio
async def test_graph_call_kill_switch(monkeypatch):
    monkeypatch.setattr(
        config,
        "read_settings",
        lambda: {"fanpage_care": {"enabled": True, "kill_switch": True}},
    )
    # Write tool bị chặn
    res = await fanpage_care_graph.call("fb_page_reply", {"comment_id": "123", "message": "test"})
    assert res.startswith("ERROR: kill_switch_active")


@pytest.mark.anyio
async def test_graph_call_readonly_perm(monkeypatch):
    monkeypatch.setattr(
        config,
        "read_settings",
        lambda: {"fanpage_care": {"enabled": True, "kill_switch": False}},
    )
    # Stub mcp_store trả connection readonly
    import mcp_store
    monkeypatch.setattr(
        mcp_store,
        "_load",
        lambda: {
            "connections": [
                {
                    "id": "c1",
                    "connector_id": "facebook-pages",
                    "label": "FB Pages",
                    "perm": "readonly",
                }
            ]
        },
    )
    res = await fanpage_care_graph.call("fb_page_reply", {"comment_id": "123", "message": "test"})
    assert res.startswith("ERROR:")
    assert "chế độ hiện tại" in res or "readonly" in res or "perm" in res


@pytest.mark.anyio
async def test_graph_call_success_and_audit(monkeypatch):
    monkeypatch.setattr(
        config,
        "read_settings",
        lambda: {"fanpage_care": {"enabled": True, "kill_switch": False, "mode": "auto"}},
    )
    import mcp_store
    monkeypatch.setattr(
        mcp_store,
        "_load",
        lambda: {
            "connections": [
                {
                    "id": "c1",
                    "connector_id": "facebook-pages",
                    "label": "FB Pages",
                    "perm": "full",
                }
            ]
        },
    )

    # Mock plugins_host call
    import plugins_host
    mock_call = AsyncMock(return_value=json.dumps({"id": "reply_123"}))
    monkeypatch.setattr(
        plugins_host,
        "plugin_tools",
        lambda mode="full", vault_root=None: ([], {"fb_page_reply": {"call": mock_call}}),
    )

    res = await fanpage_care_graph.call("fb_page_reply", {"comment_id": "123", "message": "Dạ em chào anh/chị"})
    assert "reply_123" in res

    # Audit phải ghi vào cả 2 file
    assert fanpage_care_graph._MCP_AUDIT_PATH.exists()
    assert fanpage_care_graph._CARE_AUDIT_PATH.exists()
    care_rec = json.loads(fanpage_care_graph._CARE_AUDIT_PATH.read_text(encoding="utf-8").splitlines()[-1])
    assert care_rec["ok"] is True
    assert care_rec["tool"] == "fb_page_reply"
