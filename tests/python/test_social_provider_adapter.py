"""Unit tests for Social Provider Adapter (PostPeer Gateway & Multi-Platform Publishing).

Covers:
1. PostPeer account normalization across TikTok, Instagram, YouTube, and X.
2. Capabilities matrix honesty: No inbox/comments claimed for PostPeer platforms.
3. Publish unsupported platform returns clear error.
4. Publish success writes persistent log with real/mock external_post_id.
5. RBAC: Staff publish receives 403 Forbidden, manager/owner allowed.
6. Empty logs return 0 mock posts (zero fake data).

Run:
    python -m pytest tests/python/test_social_provider_adapter.py -v
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))

import ops_rbac
import postpeer_service
from main import app


@pytest.fixture
def tmp_vault():
    td = tempfile.mkdtemp(prefix="test_social_vault_")
    vault = Path(td)
    (vault / "Javis").mkdir(parents=True, exist_ok=True)
    return vault


@pytest.fixture
def client():
    return TestClient(app, base_url="http://127.0.0.1")


def test_postpeer_account_normalization_multiple_platforms():
    """1. Test PostPeer account normalization across TikTok, Instagram, YouTube, and X."""
    raw_samples = [
        {
            "accountId": "6aa3ba9df4c58f3c57921507",
            "name": "seotrum",
            "username": "@seotrum",
            "platform": "tiktok",
            "status": "active",
            "avatarUrl": "https://p16.tiktokcdn.com/avatar.jpg",
            "connectedAt": "2026-09-01T10:00:00Z",
        },
        {
            "accountId": "6abe711bcaf6de30732c0f20",
            "name": "trannhuy.inf",
            "username": "@trannhuy.inf",
            "platform": "instagram",
            "status": "active",
            "avatarUrl": "https://instagram.fhan.net/avatar.jpg",
            "connectedAt": "2026-09-15T12:00:00Z",
        },
        {
            "accountId": "6abe70e0caf6de30732c0f1b",
            "name": "trannhuy4641",
            "username": "@trannhuy4641",
            "platform": "youtube",
            "status": "active",
            "avatarUrl": "https://yt3.ggpht.com/avatar.jpg",
            "connectedAt": "2026-09-18T08:30:00Z",
        },
        {
            "accountId": "6abe7148caf6de30732c0f21",
            "name": "RoyceDaiDe",
            "username": "@RoyceDaiDe",
            "platform": "twitter",  # PostPeer sends 'twitter', must normalize to 'x'
            "status": "active",
            "avatarUrl": "https://pbs.twimg.com/avatar.jpg",
            "connectedAt": "2026-09-20T14:15:00Z",
        },
    ]

    normalized = [postpeer_service.normalize_account_data(it) for it in raw_samples]
    assert len(normalized) == 4

    by_platform = {acc["platform"]: acc for acc in normalized}
    assert set(by_platform.keys()) == {"tiktok", "instagram", "youtube", "x"}

    # TikTok
    tt = by_platform["tiktok"]
    assert tt["username"] == "@seotrum"
    assert tt["oauth_app"] == "PostPeer"
    assert tt["social_group"] == "Game BSN"
    assert tt["capabilities"]["publish"] is True
    assert tt["capabilities"]["inbox"] is False
    assert tt["capabilities"]["comments"] is False
    assert tt["capabilities"]["analytics"] is False
    assert "Không hỗ trợ hộp thư/inbox" in tt["provider_note"]

    # Instagram
    ig = by_platform["instagram"]
    assert ig["username"] == "@trannhuy.inf"
    assert ig["capabilities"]["publish"] is True
    assert ig["capabilities"]["inbox"] is False
    assert ig["capabilities"]["comments"] is False

    # YouTube
    yt = by_platform["youtube"]
    assert yt["username"] == "@trannhuy4641"
    assert yt["capabilities"]["publish"] is True
    assert yt["capabilities"]["inbox"] is False
    assert yt["capabilities"]["comments"] is False

    # X (Twitter normalized)
    x = by_platform["x"]
    assert x["username"] == "@RoyceDaiDe"
    assert x["platform"] == "x"
    assert x["oauth_app"] == "PostPeer"
    assert x["capabilities"]["publish"] is True
    assert x["capabilities"]["inbox"] is False
    assert x["capabilities"]["comments"] is False


def test_capabilities_matrix_no_inbox_for_postpeer():
    """2. Test capabilities matrix does not claim inbox/comments for PostPeer platforms."""
    res = postpeer_service.get_social_capabilities_matrix()
    assert res.get("ok") is True
    matrix = res.get("matrix", {})

    assert "facebook" in matrix
    assert "tiktok" in matrix
    assert "instagram" in matrix
    assert "youtube" in matrix
    assert "x" in matrix

    # Meta Graph Facebook claims inbox and comments
    fb = matrix["facebook"]
    assert fb["provider"] == "meta_graph"
    assert fb["capabilities"]["publish"] is True
    assert fb["capabilities"]["inbox"] is True
    assert fb["capabilities"]["comments"] is True
    assert fb["capabilities"]["webhook"] is True

    # PostPeer platforms: publish is True, but inbox/comments/webhook are strictly False
    for p in ["tiktok", "instagram", "youtube", "x"]:
        item = matrix[p]
        assert item["provider"] == "postpeer"
        assert item["capabilities"]["publish"] is True
        assert item["capabilities"]["inbox"] is False
        assert item["capabilities"]["comments"] is False
        assert item["capabilities"]["webhook"] is False
        assert item["capabilities"]["analytics"] is False


def test_publish_unsupported_platform_error(tmp_vault):
    """3. Test publish unsupported platform returns clear error."""
    # Unsupported platform
    res = postpeer_service.publish_social_post(
        platform="threads_unsupported",
        account_id="acc_123",
        caption="Testing",
        vault_root=tmp_vault,
    )
    assert res.get("ok") is False
    assert "không hỗ trợ xuất bản" in res.get("error", "")

    # Missing account_id
    res_no_acc = postpeer_service.publish_social_post(
        platform="tiktok",
        account_id="",
        caption="Testing",
        vault_root=tmp_vault,
    )
    assert res_no_acc.get("ok") is False
    assert "Thiếu 'account_id'" in res_no_acc.get("error", "")


def test_publish_success_writes_persistent_log(monkeypatch, tmp_vault):
    """4. Test publish success writes persistent log with real/mock external_post_id."""
    monkeypatch.setenv("MOCK_POSTPEER", "1")
    monkeypatch.setenv("POSTPEER_KEY", "mock_key_test_123456")

    res = postpeer_service.publish_social_post(
        platform="x",
        account_id="6abe7148caf6de30732c0f21",
        caption="Hôm nay ra mắt tính năng Social Channels Hub!",
        media_urls=["https://trannhuy.online/images/feature.jpg"],
        brand="saoviet",
        username="@RoyceDaiDe",
        vault_root=tmp_vault,
    )

    assert res.get("ok") is True
    external_id = res.get("external_post_id")
    assert external_id is not None and len(external_id) > 0
    assert res.get("status") == "published"
    assert "permalink" in res

    # Verify persistent log in Javis/social-posts.jsonl
    log_file = tmp_vault / "Javis" / "social-posts.jsonl"
    assert log_file.is_file(), "social-posts.jsonl must be created"
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["platform"] == "x"
    assert entry["provider"] == "postpeer"
    assert entry["account_id"] == "6abe7148caf6de30732c0f21"
    assert entry["username"] == "@RoyceDaiDe"
    assert entry["caption"] == "Hôm nay ra mắt tính năng Social Channels Hub!"
    assert entry["media_count"] == 1
    assert entry["status"] == "published"
    assert entry["external_post_id"] == external_id

    # Also publish to TikTok and ensure dual-logging (social-posts.jsonl and tiktok-posts.jsonl)
    res_tt = postpeer_service.publish_social_post(
        platform="tiktok",
        account_id="6aa3ba9df4c58f3c57921507",
        caption="Video mới về hướng dẫn sử dụng Javis Ops",
        media_urls=["https://trannhuy.online/images/slide1.jpg"],
        brand="bsn",
        username="@seotrum",
        vault_root=tmp_vault,
    )
    assert res_tt.get("ok") is True
    tt_file = tmp_vault / "Javis" / "tiktok-posts.jsonl"
    assert tt_file.is_file(), "tiktok-posts.jsonl must also be created for TikTok"
    tt_lines = tt_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(tt_lines) == 1
    tt_entry = json.loads(tt_lines[0])
    assert tt_entry["accountId"] == "6aa3ba9df4c58f3c57921507"


def test_staff_publish_403_forbidden(monkeypatch, client):
    """5. Test staff calling publish returns 403 Forbidden, manager/owner allowed."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="test_social_rbac_"))
    users_file = tmp_dir / "ops_users.json"
    sess_file = tmp_dir / "ops_sessions.json"
    monkeypatch.setattr(ops_rbac, "OPS_USERS_FILE", users_file)
    monkeypatch.setattr(ops_rbac, "OPS_SESSIONS_FILE", sess_file)
    monkeypatch.setattr(ops_rbac, "_OPS_SESSIONS", {})
    monkeypatch.delenv("JAVIS_REQUIRE_LOGIN", raising=False)
    monkeypatch.delenv("JAVIS_OPS_DEMO_AUTO_OWNER", raising=False)

    # Unit-level check_access_permission check
    staff_user = {"role": "staff", "username": "nhanvien"}
    allowed_staff, reason_staff = ops_rbac.check_access_permission(staff_user, "/ops/social/publish", "POST")
    assert allowed_staff is False
    assert "không có quyền" in reason_staff

    manager_user = {"role": "manager", "username": "truongnhom"}
    allowed_mgr, reason_mgr = ops_rbac.check_access_permission(manager_user, "/ops/social/publish", "POST")
    assert allowed_mgr is True
    assert reason_mgr is None

    owner_user = {"role": "owner", "username": "admin"}
    allowed_owner, reason_owner = ops_rbac.check_access_permission(owner_user, "/ops/social/publish", "POST")
    assert allowed_owner is True
    assert reason_owner is None

    # HTTP-level check via FastAPI client
    # 1. Staff session
    tok_staff = ops_rbac.create_session("u_staff", "nhanvien", "staff", "Nhân Viên")
    client.cookies.set("ops_session", tok_staff)
    res_staff = client.post(
        "/ops/social/publish",
        json={"platform": "tiktok", "account_id": "acc_1", "caption": "test"},
    )
    assert res_staff.status_code == 403
    assert "không có quyền" in res_staff.text.lower() or "forbidden" in res_staff.text.lower()

    # 2. Manager session (allowed to pass RBAC check)
    tok_mgr = ops_rbac.create_session("u_mgr", "truongnhom", "manager", "Trưởng Nhóm")
    client.cookies.set("ops_session", tok_mgr)
    monkeypatch.setenv("MOCK_POSTPEER", "1")
    monkeypatch.setenv("POSTPEER_KEY", "mock_key")
    res_mgr = client.post(
        "/ops/social/publish",
        json={"platform": "x", "account_id": "acc_1", "caption": "manager post"},
    )
    # Manager passes RBAC: status is 200 (or 400 if bad payload, but not 403!)
    assert res_mgr.status_code in (200, 400)
    assert res_mgr.status_code != 403


def test_empty_logs_returns_zero_mock_posts(tmp_vault):
    """6. Test empty logs return 0 mock posts (zero fake metrics or fabricated posts)."""
    # In an empty vault with no files
    posts = postpeer_service.get_social_posts(vault_root=tmp_vault)
    assert isinstance(posts, list)
    assert len(posts) == 0

    posts_tt = postpeer_service.get_social_posts(platform="tiktok", vault_root=tmp_vault)
    assert len(posts_tt) == 0

    posts_x = postpeer_service.get_social_posts(platform="x", vault_root=tmp_vault)
    assert len(posts_x) == 0
