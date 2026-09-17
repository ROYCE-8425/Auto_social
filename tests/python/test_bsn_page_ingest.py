"""Page Game Giá Rẻ BSN (343562028848465) phải nằm trong eligible + poll đúng page."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_real_bsn_kit_in_repo():
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    from fanpage_care import list_eligible_pages, _load_kit_for_page
    from brand_kit import parse_brand_kit_channels, detect_brand_from_kit

    vault = ROOT / "brains" / "Brain Default"
    kit = vault / "wiki" / "brand-kits" / "game-gia-re-bsn.md"
    assert kit.is_file()
    parsed = parse_brand_kit_channels(kit)
    assert parsed.brand == "bsn"
    assert parsed.facebook.ids.get("page_id") == "343562028848465"
    assert parsed.facebook.enabled is True

    pages = list_eligible_pages(vault)
    bsn = [p for p in pages if p["page_id"] == "343562028848465"]
    assert len(bsn) == 1
    assert bsn[0]["brand"] == "bsn"
    assert "BSN" in bsn[0]["name"].upper() or "game" in bsn[0]["name"].lower()

    loaded = _load_kit_for_page(vault, "343562028848465")
    assert loaded is not None
    assert loaded["brand"] == "bsn"
    assert detect_brand_from_kit(loaded["file"]) == "bsn"


@pytest.mark.anyio
async def test_poll_tick_only_bsn_page(monkeypatch, tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    import config
    import fanpage_care
    import fanpage_care_graph
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
    (kits / "thsv-q7.md").write_text(
        "# Kit\n- Tên Fanpage: Q7\n- Page ID: 108426965133947\n",
        encoding="utf-8",
    )
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(store, "DEFAULT_DB_PATH", state / "care.sqlite3")
    monkeypatch.setattr(config, "read_settings", lambda: {"fanpage_care": {"enabled": False}})

    called = []

    async def fake_call(tool, args, **kwargs):
        called.append(args.get("page_id"))
        return json.dumps({
            "items": [{
                "comment_id": "c_bsn_1",
                "from_id": "user1",
                "from_name": "Ae gamer",
                "message": "Key steam bảo hành thế nào shop ơi",
                "post_id": "p1",
            }]
        })

    monkeypatch.setattr(fanpage_care.fanpage_care_graph, "call", fake_call)

    feat = fanpage_care.FanpageCareFeature(fanpage_care.FanpageCareDeps(vault_root=vault))
    res = await feat.poll_tick(page_id="343562028848465", force_ingest=True)
    assert res.get("reason") != "disabled"
    assert called == ["343562028848465"]
    assert res["events_ingested"] >= 1


def test_record_event_iso_string_timestamp(tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    import fanpage_care_store as store

    db = tmp_path / "test_iso.sqlite3"
    ev_id, is_new = store.record_event({
        "kind": "comment",
        "platform": "facebook",
        "page_id": "343562028848465",
        "object_id": "c_iso_test_1",
        "created_ts": "2026-09-15T06:56:47+0000",
        "body": "Test comment with ISO timestamp",
    }, db_path=db)

    assert is_new is True
    events = store.list_events(db_path=db)
    assert len(events) == 1
    assert isinstance(events[0]["created_ts"], float)
    assert events[0]["created_ts"] > 1700000000

