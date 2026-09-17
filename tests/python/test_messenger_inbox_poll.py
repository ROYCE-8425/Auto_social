"""Kéo hộp thư Business (Messenger) → ingest + phân loại."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.anyio
async def test_poll_messenger_ingests_customer_message(monkeypatch, tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    import config
    import fanpage_care
    import fanpage_care_store as store

    vault = tmp_path / "vault"
    kits = vault / "wiki" / "brand-kits"
    kits.mkdir(parents=True)
    (kits / "game-gia-re-bsn.md").write_text(
        (ROOT / "brains" / "Brain Default" / "wiki" / "brand-kits" / "game-gia-re-bsn.md").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", state / "care.sqlite3")
    monkeypatch.setattr(config, "read_settings", lambda: {"fanpage_care": {"enabled": False, "mode": "suggest"}})

    async def fake_call(tool, args, **kwargs):
        if tool == "fb_conversations":
            return json.dumps({"data": [{"id": "t_1", "snippet": "key steam"}]})
        if tool == "fb_conversation_thread":
            return json.dumps({
                "data": [{
                    "id": "m_99",
                    "from": {"id": "psid_user", "name": "Ae"},
                    "to": {"data": [{"id": "343562028848465"}]},
                    "message": "Shop ơi key steam bảo hành thế nào",
                    "created_time": "2026-09-16T10:00:00+0000",
                }]
            })
        return json.dumps({"items": []})

    monkeypatch.setattr(fanpage_care.fanpage_care_graph, "call", fake_call)

    feat = fanpage_care.FanpageCareFeature(fanpage_care.FanpageCareDeps(vault_root=vault))
    res = await feat.poll_tick(
        page_id="343562028848465", force_ingest=True, channel="messenger",
    )
    assert res.get("reason") != "disabled"
    assert res.get("messages_ingested", 0) >= 1
    evs = store.list_events(platform="messenger")
    assert evs
    assert evs[0]["kind"] == "message"
    assert "steam" in (evs[0].get("body") or "").lower()


def test_customer_behavior_counts_messages(tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    import fanpage_care_store as store

    monkeypatch.setattr(store, "DEFAULT_DB_PATH", tmp_path / "care.sqlite3")
    store.init_db()
    ev_id, _ = store.record_event({
        "kind": "message",
        "platform": "messenger",
        "page_id": "343562028848465",
        "object_id": "m1",
        "from_id": "psid1",
        "thread_id": "psid1",
        "body": "ib mua key",
        "class": "lead",
        "created_ts": __import__("time").time(),
    })
    cust, _ = store.get_or_create_customer(name="Ae", page_id="343562028848465", psid="psid1", tag="lead")
    b = store.customer_behavior(cust["crm_id"])
    assert b["message_count"] >= 1
    assert b["stage"] in ("lead", "dang_tu_van", "moi_tiep_can")
