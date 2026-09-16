"""Unit tests for PostPeer TikTok connector and bundled plugin.
Run:
    python -m pytest tests/python/test_postpeer_tiktok.py -v
"""
import asyncio
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-postpeer-"))

import pytest
import mcp_catalog


def test_catalog_postpeer_entry():
    cat = json.load(open(ROOT / "system" / "mcp-catalog.json", encoding="utf-8"))
    pp = next((x for x in cat["connectors"] if x["id"] == "postpeer"), None)
    assert pp is not None, "mcp-catalog.json must contain 'postpeer' connector"
    assert pp["auth"]["type"] == "apikey"
    assert any(f["key"] == "postpeer_key" for f in pp["auth"]["fields"])
    assert pp["default_perm"] == "readonly"
    assert "postpeer_tiktok_post" in pp["tool_meta"]["danger"]
    assert "postpeer_accounts" in pp["tool_meta"]["read"]
    assert "postpeer_tiktok_creator" in pp["tool_meta"]["read"]
    assert "postpeer_post_get" in pp["tool_meta"]["read"]

    # Verify via mcp_catalog module
    entry = mcp_catalog.get("postpeer")
    assert entry is not None
    assert entry["id"] == "postpeer"


def test_plugin_registration():
    plugin_path = ROOT / "system" / "plugins" / "postpeer-tiktok" / "plugin.py"
    assert plugin_path.is_file(), "plugin.py must exist"

    spec = importlib.util.spec_from_file_location("postpeer_tiktok_test", str(plugin_path))
    plug = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plug)

    class MockContext:
        def __init__(self):
            self.tools = []

        def register_tool(self, name, description, handler, schema=None, min_mode="readonly", check_fn=None, **k):
            self.tools.append({"name": name, "min_mode": min_mode, "check_fn": check_fn})

    ctx = MockContext()
    plug.register(ctx)

    assert len(ctx.tools) == 4
    tool_map = {t["name"]: t for t in ctx.tools}
    assert "postpeer_accounts" in tool_map
    assert tool_map["postpeer_accounts"]["min_mode"] == "readonly"

    assert "postpeer_tiktok_creator" in tool_map
    assert tool_map["postpeer_tiktok_creator"]["min_mode"] == "readonly"

    assert "postpeer_post_get" in tool_map
    assert tool_map["postpeer_post_get"]["min_mode"] == "readonly"

    assert "postpeer_tiktok_post" in tool_map
    assert tool_map["postpeer_tiktok_post"]["min_mode"] == "full"

    # Test check_fn when no token configured
    plug._token = lambda: None
    err = plug._check()
    assert err is not None
    assert "Chưa kết nối PostPeer" in err


def test_plugin_mock_accounts_and_creator():
    async def _run():
        spec = importlib.util.spec_from_file_location("postpeer_tiktok_test2", str(ROOT / "system" / "plugins" / "postpeer-tiktok" / "plugin.py"))
        plug = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plug)

        plug._token = lambda: "test_pp_key_123"

        # Mock accounts
        async def mock_get_accounts(token):
            return [
                {
                    "accountId": "acc_tt_123456",
                    "platform": "tiktok",
                    "username": "@tinhocsaoviet",
                    "avatarUrl": "https://p16.tiktokcdn.com/avatar.jpg",
                    "status": "active",
                }
            ]

        plug._get_accounts = mock_get_accounts

        res_accounts = await plug._handle_accounts({}, None)
        data = json.loads(res_accounts)
        assert "accounts" in data
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["accountId"] == "acc_tt_123456"
        assert data["accounts"][0]["username"] == "@tinhocsaoviet"

        # Mock creator info
        async def mock_get_creator(token, account_id):
            assert account_id == "acc_tt_123456"
            return {
                "privacyLevelOptions": ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
                "commentDisabled": False,
                "duetDisabled": False,
                "stitchDisabled": False,
            }

        plug._get_creator_info = mock_get_creator

        res_creator = await plug._handle_creator({"account_id": "acc_tt_123456"}, None)
        c_data = json.loads(res_creator)
        assert "creator_info" in c_data

    asyncio.run(_run())


def test_plugin_mock_post_flow():
    async def _run():
        spec = importlib.util.spec_from_file_location("postpeer_tiktok_test3", str(ROOT / "system" / "plugins" / "postpeer-tiktok" / "plugin.py"))
        plug = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plug)

        plug._token = lambda: "test_pp_key_123"

        # 1. Validation: reject non-https video url
        err_local = await plug._handle_tiktok_post({
            "account_id": "acc_tt_123456",
            "video": "attachments/dataset/video.mp4",
            "caption": "Test video",
        }, None)
        assert "ERROR: Cần URL https công khai" in err_local

        # 2. Mock success post
        async def mock_creator(token, account_id):
            return {"privacyLevelOptions": ["PUBLIC_TO_EVERYONE"]}

        async def mock_post_media(token, payload):
            assert payload["platforms"][0]["accountId"] == "acc_tt_123456"
            assert payload["platforms"][0]["platformSpecificData"]["privacyLevel"] == "PUBLIC_TO_EVERYONE"
            assert payload["mediaItems"][0]["url"] == "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/sample.mp4"
            return {
                "id": "post_789012",
                "postUrl": "https://www.tiktok.com/@tinhocsaoviet/video/789012",
                "status": "published",
            }

        plug._get_creator_info = mock_creator
        plug._post_media = mock_post_media

        res = await plug._handle_tiktok_post({
            "account_id": "acc_tt_123456",
            "video": "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/sample.mp4",
            "caption": "Mẹo Excel hữu ích #TinhocSaoViet #Excel",
        }, None)
        res_data = json.loads(res)
        assert res_data["ok"] is True
        assert res_data["postpeer_id"] == "post_789012"
        assert "tiktok.com" in res_data["tiktok_url"]
        assert res_data["draft"] is False

        # 3. Mock 402 out of credit
        async def mock_post_media_402(token, payload):
            return {
                "__error": "Hết credit trên PostPeer (402 Payment Required). Vui lòng nạp thêm credit trên postpeer.dev để tiếp tục đăng video.",
                "__code": 402,
            }

        plug._post_media = mock_post_media_402

        res_402 = await plug._handle_tiktok_post({
            "account_id": "acc_tt_123456",
            "video": "https://laptrinhpython.tinhocsaoviet.com/storage/videos/ready/sample.mp4",
            "caption": "Mẹo Excel hữu ích #TinhocSaoViet #Excel",
        }, None)
        assert "ERROR: Hết credit trên PostPeer" in res_402

    asyncio.run(_run())
