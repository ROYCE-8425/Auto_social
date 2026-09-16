# -*- coding: utf-8 -*-
"""Test platform column, migration and filtering in fanpage_care_store."""
import sys
import tempfile
import time
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from server import fanpage_care_store as store


def test_platform_column_and_migration():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "test_platform.sqlite3"

        # 1. Init DB fresh
        store.init_db(db_path)

        # 2. Record Facebook comment
        id_fb, new_fb = store.record_event({
            "kind": "comment",
            "platform": "facebook",
            "page_id": "P_SAOVIET",
            "object_id": "c_fb_1",
            "body": "hoc phi tin hoc bao nhieu",
            "class": "lead",
        }, db_path=db_path)
        assert new_fb is True
        assert id_fb > 0

        # 3. Record Messenger message
        id_msg, new_msg = store.record_event({
            "kind": "message",
            "platform": "messenger",
            "page_id": "P_SAOVIET",
            "object_id": "m_msg_1",
            "body": "Em muon tu van khoa ke toan",
            "class": "lead",
        }, db_path=db_path)
        assert new_msg is True
        assert id_msg > 0

        # 4. Record TikTok comment (future / mock)
        id_tt, new_tt = store.record_event({
            "kind": "comment",
            "platform": "tiktok",
            "page_id": "TT_BSN",
            "object_id": "c_tt_1",
            "body": "gia game wukong bn shop",
            "class": "lead",
        }, db_path=db_path)
        assert new_tt is True

        # 5. Default platform fallback when missing or unknown
        id_def, _ = store.record_event({
            "kind": "comment",
            "platform": "invalid_platform",
            "page_id": "P_DEF",
            "object_id": "c_def_1",
            "body": "test fallback",
        }, db_path=db_path)

        # 6. Test list_events with platform filter
        all_events = store.list_events(db_path=db_path)
        assert len(all_events) == 4

        fb_events = store.list_events(platform="facebook", db_path=db_path)
        # c_fb_1 and c_def_1 (fallback to facebook)
        assert len(fb_events) == 2
        for ev in fb_events:
            assert ev["platform"] == "facebook"

        tt_events = store.list_events(platform="tiktok", db_path=db_path)
        assert len(tt_events) == 1
        assert tt_events[0]["object_id"] == "c_tt_1"
        assert tt_events[0]["platform"] == "tiktok"

        msg_events = store.list_events(platform="messenger", db_path=db_path)
        assert len(msg_events) == 1
        assert msg_events[0]["object_id"] == "m_msg_1"
        assert msg_events[0]["platform"] == "messenger"


def test_platform_migration_on_legacy_schema():
    """Test that existing tables without platform column are migrated safely."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "test_legacy.sqlite3"
        conn = store.get_connection(db_path)
        # Create legacy table without platform column
        conn.executescript("""
        CREATE TABLE events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          kind TEXT NOT NULL,
          page_id TEXT NOT NULL,
          object_id TEXT NOT NULL,
          thread_id TEXT,
          from_id TEXT,
          from_name TEXT,
          body TEXT,
          class TEXT,
          faq_intent TEXT,
          created_ts REAL,
          ingested_ts REAL,
          UNIQUE(kind, object_id)
        );
        INSERT INTO events (kind, page_id, object_id, body) VALUES ('comment', 'P1', 'c_old_1', 'old text');
        """)
        conn.close()

        # Call init_db - must run migration ALTER TABLE ADD COLUMN platform
        store.init_db(db_path)

        # Verify old row has default 'facebook'
        rows = store.list_events(db_path=db_path)
        assert len(rows) == 1
        assert rows[0]["platform"] == "facebook"

        # Now insert new event with platform=tiktok
        store.record_event({
            "kind": "comment",
            "platform": "tiktok",
            "page_id": "P_TT",
            "object_id": "c_tt_2",
            "body": "hello tiktok",
        }, db_path=db_path)

        tt_events = store.list_events(platform="tiktok", db_path=db_path)
        assert len(tt_events) == 1
        assert tt_events[0]["object_id"] == "c_tt_2"
