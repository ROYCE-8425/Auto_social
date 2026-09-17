# -*- coding: utf-8 -*-
"""Test care scoping, feature toggles and auto-reply safety."""
import sys
import tempfile
import time
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from server import fanpage_care as care
from server import fanpage_care_store as store


def test_pages_in_scope():
    eligible = [
        {"page_id": "343562028848465", "name": "Game BSN", "brand": "bsn"},
        {"page_id": "988656934325292", "name": "Sao Viet Q7", "brand": "saoviet"},
        {"page_id": "111222333444555", "name": "Sao Viet Thu Duc", "brand": "saoviet"},
    ]

    # 1. Scope all
    cfg_all = {"scope": "all"}
    res_all = care.pages_in_scope(cfg_all, eligible)
    assert len(res_all) == 3

    # 2. Scope brand BSN
    cfg_bsn = {"scope": "brand", "scope_brand": "bsn"}
    res_bsn = care.pages_in_scope(cfg_bsn, eligible)
    assert len(res_bsn) == 1
    assert res_bsn[0]["page_id"] == "343562028848465"

    # 3. Scope brand Sao Viet
    cfg_sv = {"scope": "brand", "scope_brand": "saoviet"}
    res_sv = care.pages_in_scope(cfg_sv, eligible)
    assert len(res_sv) == 2
    assert {p["page_id"] for p in res_sv} == {"988656934325292", "111222333444555"}

    # 4. Scope single page
    cfg_pg = {"scope": "page", "scope_page_id": "988656934325292"}
    res_pg = care.pages_in_scope(cfg_pg, eligible)
    assert len(res_pg) == 1
    assert res_pg[0]["name"] == "Sao Viet Q7"


def test_feat_on_hierarchy():
    cfg = {
        "features": {
            "poll_comments": True,
            "poll_messenger": True,
            "auto_reply_comments": False,
            "auto_reply_messenger": False,
            "hide_spam": False,
        },
        "pages": {
            "343562028848465": {
                "enabled": True,
                "features": {
                    "auto_reply_comments": True,  # Page overrides global False to True
                },
            },
            "988656934325292": {
                "enabled": True,
                "features": {
                    "poll_comments": False,  # Page overrides global True to False
                },
            },
        },
    }

    # BSN page overrides auto_reply_comments to True
    assert care.feat_on(cfg, "343562028848465", "auto_reply_comments", False) is True
    # BSN page inherits poll_comments True from global
    assert care.feat_on(cfg, "343562028848465", "poll_comments", False) is True
    # BSN page inherits auto_reply_messenger False from global
    assert care.feat_on(cfg, "343562028848465", "auto_reply_messenger", False) is False

    # Sao Viet page overrides poll_comments to False
    assert care.feat_on(cfg, "988656934325292", "poll_comments", True) is False
    # Sao Viet page inherits auto_reply_comments False from global
    assert care.feat_on(cfg, "988656934325292", "auto_reply_comments", False) is False

    # Unlisted page falls back to global
    assert care.feat_on(cfg, "999999999999999", "poll_comments", False) is True
    assert care.feat_on(cfg, "999999999999999", "auto_reply_comments", False) is False

    # Unknown feature falls back to default
    assert care.feat_on(cfg, "343562028848465", "non_existent_feature", True) is True


def test_deep_merge_dict():
    base = {
        "enabled": True,
        "features": {"poll_comments": True, "poll_messenger": True, "auto_reply_comments": False},
        "pages": {
            "p1": {"enabled": True, "features": {"auto_reply_comments": False}},
            "p2": {"enabled": True},
        },
    }

    # Patch updating only p1's auto_reply_comments and global hide_spam
    patch = {
        "features": {"hide_spam": True},
        "pages": {
            "p1": {"features": {"auto_reply_comments": True}},
        },
    }

    merged = care._deep_merge_dict(base, patch)

    # p2 was preserved
    assert "p2" in merged["pages"]
    assert merged["pages"]["p2"]["enabled"] is True
    # p1 enabled was preserved
    assert merged["pages"]["p1"]["enabled"] is True
    # p1 auto_reply_comments updated
    assert merged["pages"]["p1"]["features"]["auto_reply_comments"] is True
    # global poll_comments preserved
    assert merged["features"]["poll_comments"] is True
    # global hide_spam added
    assert merged["features"]["hide_spam"] is True


def test_scoped_stats_and_lists():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "test_scope.sqlite3"
        store.init_db(db_path)

        now = time.time()
        # Page 1 (BSN)
        store.record_event({
            "kind": "comment", "platform": "facebook", "page_id": "BSN_1",
            "object_id": "c_bsn_1", "body": "gia game wukong bn", "class": "faq",
            "created_ts": now, "ingested_ts": now,
        }, db_path=db_path)
        store.record_event({
            "kind": "message", "platform": "messenger", "page_id": "BSN_1",
            "object_id": "m_bsn_1", "body": "tu van game", "class": "lead",
            "created_ts": now, "ingested_ts": now,
        }, db_path=db_path)

        # Page 2 (Sao Viet)
        store.record_event({
            "kind": "comment", "platform": "facebook", "page_id": "SV_1",
            "object_id": "c_sv_1", "body": "hoc phi tin hoc", "class": "lead",
            "created_ts": now, "ingested_ts": now,
        }, db_path=db_path)

        # Drafts
        store.create_draft(1, "BSN_1", "c_bsn_1", "Da bao gia game", "faq", db_path=db_path)
        store.create_draft(3, "SV_1", "c_sv_1", "Da bao hoc phi", "lead", db_path=db_path)

        # Actions
        store.record_action(1, "reply", "c_bsn_1", "auto", "care-worker", db_path=db_path)

        # 1. Global stats
        st_all = store.get_stats(db_path=db_path)
        assert st_all["total_events"] == 3
        assert st_all["events_24h"] == 3
        assert st_all["leads_24h"] == 2
        assert st_all["replies_24h"] == 1
        assert st_all["pending_drafts"] == 2

        # 2. Scoped to BSN_1
        st_bsn = store.get_stats(page_ids=["BSN_1"], db_path=db_path)
        assert st_bsn["total_events"] == 2
        assert st_bsn["events_24h"] == 2
        assert st_bsn["leads_24h"] == 1
        assert st_bsn["replies_24h"] == 1
        assert st_bsn["pending_drafts"] == 1
        assert st_bsn["pending_comment_drafts"] == 1

        # 3. Scoped to SV_1
        st_sv = store.get_stats(page_ids=["SV_1"], db_path=db_path)
        assert st_sv["total_events"] == 1
        assert st_sv["events_24h"] == 1
        assert st_sv["leads_24h"] == 1
        assert st_sv["replies_24h"] == 0
        assert st_sv["pending_drafts"] == 1

        # 4. Scoped to empty list
        st_empty = store.get_stats(page_ids=[], db_path=db_path)
        assert st_empty["total_events"] == 0
        assert st_empty["events_24h"] == 0

        # 5. List events with page_ids
        evs_bsn = store.list_events(page_ids=["BSN_1"], db_path=db_path)
        assert len(evs_bsn) == 2
        assert all(e["page_id"] == "BSN_1" for e in evs_bsn)

        # 6. List drafts with page_ids
        dfs_sv = store.list_drafts(page_ids=["SV_1"], db_path=db_path)
        assert len(dfs_sv) == 1
        assert dfs_sv[0]["page_id"] == "SV_1"


import pytest

@pytest.mark.anyio
async def test_auto_reply_safety(monkeypatch):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        vault_root = Path(tmp_dir) / "vault"
        vault_root.mkdir(parents=True, exist_ok=True)
        db_path = Path(tmp_dir) / "test_safety.sqlite3"
        monkeypatch.setattr(store, "DEFAULT_DB_PATH", db_path)
        monkeypatch.setattr(care.store, "DEFAULT_DB_PATH", db_path)
        care.store.init_db()

        deps = care.FanpageCareDeps(vault_root=str(vault_root), brain="test")
        feat = care.FanpageCareFeature(deps)

        t_seed = int(time.time())
        # 1. mode="suggest", auto_reply_comments=True -> MUST create draft, not reply
        cfg_suggest = {
            "enabled": True,
            "mode": "suggest",
            "features": {"auto_reply_comments": True, "auto_reply_messenger": True},
        }
        res1 = await feat.process_inbound_comment(
            "P1", f"c_sug_{t_seed}", "post1", None, "u1", "User 1", "hoc phi the nao", None,
            cfg=cfg_suggest,
        )
        assert res1.get("status") == "ok"
        assert res1.get("replied") is False
        assert res1.get("draft_created") is True

        # 2. mode="auto", auto_reply_comments=False -> MUST create draft, not reply
        cfg_auto_off = {
            "enabled": True,
            "mode": "auto",
            "features": {"auto_reply_comments": False, "auto_reply_messenger": False},
        }
        res2 = await feat.process_inbound_comment(
            "P1", f"c_auto_{t_seed}", "post1", None, "u2", "User 2", "hoc phi the nao", None,
            cfg=cfg_auto_off,
        )
        assert res2.get("status") == "ok"
        assert res2.get("replied") is False
        assert res2.get("draft_created") is True

        # 3. messenger: mode="suggest", auto_reply_messenger=True -> MUST create draft, not send
        care.store.update_messaging_window("P1", f"psid_{t_seed}", is_user=True, user_ts=time.time())
        msg_item = {
            "sender": {"id": f"psid_{t_seed}", "name": "User 3"},
            "recipient": {"id": "P1"},
            "timestamp": time.time() * 1000,
            "message": {"mid": f"mid_{t_seed}", "text": "em muon hoi hoc phi"},
        }
        res3 = await feat.process_inbound_message(
            "P1", msg_item, cfg=cfg_suggest,
        )
        assert res3.get("replied") is False
        assert res3.get("draft_created") is True


def test_separation_comment_vs_messenger_drafts():
    """Verify strict kind separation: comment drafts must never leak into messenger, and vice versa."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "test_separation.sqlite3"
        store.init_db(db_path)
        now = time.time()

        # 1. Event: comment on Facebook post
        ev_cmt_id, _ = store.record_event({
            "kind": "comment", "platform": "facebook", "page_id": "P_TEST",
            "object_id": "post1_cmt123", "body": "Khoa hoc nay hoc phi the nao?",
            "class": "lead", "from_name": "Tran Nhu Y", "from_id": "user_cmt_1",
            "created_ts": now, "ingested_ts": now,
        }, db_path=db_path)

        # 2. Event: message on Messenger (pure numeric PSID like 283849182391823)
        ev_msg_id, _ = store.record_event({
            "kind": "message", "platform": "messenger", "page_id": "P_TEST",
            "object_id": "283849182391823", "body": "Shop con ban acc wukong khong?",
            "class": "lead", "from_name": "Quoc Khanh", "from_id": "283849182391823",
            "created_ts": now, "ingested_ts": now,
        }, db_path=db_path)

        # 3. Create drafts for each
        dr_cmt_id = store.create_draft(ev_cmt_id, "P_TEST", "post1_cmt123", "Chao ban, hoc phi la 1tr2", "lead", db_path=db_path)
        dr_msg_id = store.create_draft(ev_msg_id, "P_TEST", "283849182391823", "Chao Quoc Khanh, shop con acc nha", "lead", db_path=db_path)

        # 4. Create an orphaned draft (no event_id) - e.g. from a test script
        dr_orphan_id = store.create_draft(None, "P_TEST", "some_random_id_123", "Orphaned draft", "lead", db_path=db_path)

        # Query kind=comment
        cmt_drafts = store.list_drafts(page_ids=["P_TEST"], status="pending", kind="comment", db_path=db_path)
        assert len(cmt_drafts) == 1
        assert cmt_drafts[0]["id"] == dr_cmt_id
        assert cmt_drafts[0]["event_kind"] == "comment"
        assert cmt_drafts[0]["from_name"] == "Tran Nhu Y"

        # Query kind=message
        msg_drafts = store.list_drafts(page_ids=["P_TEST"], status="pending", kind="message", db_path=db_path)
        assert len(msg_drafts) == 1
        assert msg_drafts[0]["id"] == dr_msg_id
        assert msg_drafts[0]["event_kind"] == "message"
        assert msg_drafts[0]["from_name"] == "Quoc Khanh"

        # Query stats
        stats = store.get_stats(page_ids=["P_TEST"], db_path=db_path)
        assert stats["pending_comment_drafts"] == 1
        assert stats["pending_message_drafts"] == 1
        assert stats["pending_drafts"] == 3  # total includes orphaned

