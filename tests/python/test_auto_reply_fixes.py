"""Unit tests cho các sửa đổi auto-reply của Javis Fanpage Care:
- Phân loại chao_hoi
- Render template BSN mới
- Auto-reply comment fallback khi mode full
- Auto-reply message và không bị kẹt takeover cũ
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_classify_greeting_as_faq_chao_hoi():
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    from fanpage_care_classify import classify_comment

    for txt in ["hi", "hello", "alo shop", "chào shop", "shop ơi"]:
        res_bsn = classify_comment(txt, brand="bsn")
        assert res_bsn["class"] == "faq", f"Failed for '{txt}': {res_bsn}"
        assert res_bsn["faq_intent"] == "chao_hoi", f"Failed for '{txt}': {res_bsn}"

        res_sv = classify_comment(txt, brand="saoviet")
        assert res_sv["class"] == "faq", f"Failed for '{txt}': {res_sv}"
        assert res_sv["faq_intent"] == "chao_hoi", f"Failed for '{txt}': {res_sv}"


def test_render_bsn_new_templates():
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    from fanpage_care_ground import render_template

    kit_path = ROOT / "brains" / "Brain Default" / "wiki" / "brand-kits" / "game-gia-re-bsn.md"
    kit = {
        "file": "game-gia-re-bsn.md",
        "brand": "bsn",
        "name": "Game Giá Rẻ BSN",
        "hotline": "0877 104 996",
        "md": kit_path.read_text(encoding="utf-8"),
    }

    for key in ["chao_hoi", "bao_hanh", "key_steam", "viet_hoa", "cai_dat"]:
        tpl = render_template(key, kit)
        assert tpl is not None, f"Template {key} is None"
        assert len(tpl) > 10, f"Template {key} too short: {tpl}"
        assert "0877 104 996" in tpl


@pytest.mark.anyio
async def test_historical_echo_does_not_lock_takeover(monkeypatch, tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    import fanpage_care
    import fanpage_care_store as store

    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", state / "care.sqlite3")
    store.init_db()

    feat = fanpage_care.FanpageCareFeature(fanpage_care.FanpageCareDeps(vault_root=tmp_path))

    pid = "343562028848465"
    psid = "user_123"

    # Tin nhắn echo cũ hơn 5 phút (ví dụ 10 phút trước)
    old_ts_ms = int((time.time() - 600) * 1000)
    item_old = {
        "sender": {"id": pid, "name": "Page"},
        "recipient": {"id": psid},
        "timestamp": old_ts_ms,
        "message": {"mid": "m_old", "text": "Tin cũ", "is_echo": True},
    }

    res = await feat.process_inbound_message(pid, item_old, cfg={"enabled": True, "mode": "full"})
    assert not res.get("takeover_activated")
    assert not store.is_under_takeover(pid, psid)


@pytest.mark.anyio
async def test_inbound_message_auto_replies_greeting(monkeypatch, tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    import fanpage_care
    import fanpage_care_store as store

    vault = tmp_path / "vault"
    kits = vault / "wiki" / "brand-kits"
    kits.mkdir(parents=True)
    kit_content = (ROOT / "brains" / "Brain Default" / "wiki" / "brand-kits" / "game-gia-re-bsn.md").read_text(encoding="utf-8")
    (kits / "game-gia-re-bsn.md").write_text(kit_content, encoding="utf-8")

    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", state / "care.sqlite3")
    store.init_db()

    sent_calls = []

    async def fake_call(tool, args, **kwargs):
        if tool == "fb_message_send":
            sent_calls.append(args)
            return json.dumps({"recipient_id": args["recipient_id"], "message_id": "mid_out"})
        return json.dumps({})

    monkeypatch.setattr(fanpage_care.fanpage_care_graph, "call", fake_call)

    feat = fanpage_care.FanpageCareFeature(fanpage_care.FanpageCareDeps(vault_root=vault))

    pid = "343562028848465"
    psid = "user_greeting"

    cfg = {
        "enabled": True,
        "mode": "full",
        "quiet_hours": "00-00",
        "features": {"auto_reply_messenger": True},
    }

    item = {
        "sender": {"id": psid, "name": "Khách Test"},
        "recipient": {"id": pid},
        "timestamp": int(time.time() * 1000),
        "message": {"mid": "m_test_greet", "text": "hi shop ơi", "is_echo": False},
    }

    res = await feat.process_inbound_message(pid, item, cfg=cfg)
    assert res.get("replied") is True
    assert len(sent_calls) == 1
    assert "Game Giá Rẻ BSN" in sent_calls[0]["message"]


@pytest.mark.anyio
async def test_inbound_comment_auto_replies_fallback(monkeypatch, tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    import fanpage_care
    import fanpage_care_store as store
    import aux_engine

    vault = tmp_path / "vault"
    kits = vault / "wiki" / "brand-kits"
    kits.mkdir(parents=True)
    kit_content = (ROOT / "brains" / "Brain Default" / "wiki" / "brand-kits" / "game-gia-re-bsn.md").read_text(encoding="utf-8")
    (kits / "game-gia-re-bsn.md").write_text(kit_content, encoding="utf-8")

    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", state / "care.sqlite3")
    store.init_db()

    replies = []

    async def fake_graph_call(tool, args, **kwargs):
        if tool == "fb_page_reply":
            replies.append(args)
            return json.dumps({"id": "comment_reply_123"})
        return json.dumps({})

    monkeypatch.setattr(fanpage_care.fanpage_care_graph, "call", fake_graph_call)

    # Giả lập complete_json bị từ chối
    async def fake_complete_json(*args, **kwargs):
        return {"refuse": True, "error": "simulated refuse"}

    monkeypatch.setattr(aux_engine, "complete_json", fake_complete_json)

    feat = fanpage_care.FanpageCareFeature(fanpage_care.FanpageCareDeps(vault_root=vault))

    pid = "343562028848465"
    cid = "comm_123"
    post_id = "post_123"

    cfg = {
        "enabled": True,
        "mode": "full",
        "quiet_hours": "00-00",
        "features": {"auto_reply_comments": True},
    }

    res = await feat.process_inbound_comment(
        pid, cid, post_id, parent_id=None, from_id="user_comm", from_name="Khách Comment",
        body="cho em hỏi chút về game", cfg=cfg,
    )

    assert res.get("replied") is True
    assert len(replies) == 1
    assert "0877 104 996" in replies[0]["message"]

