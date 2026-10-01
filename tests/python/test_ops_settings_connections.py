import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    # Use 127.0.0.1 to pass CSRF validation
    return TestClient(app, base_url="http://127.0.0.1")


def test_platform_capabilities_matrix_contract(client):
    """
    Kiem tra contract cho Platform Connections va Capabilities Matrix:
    1. Facebook: Account connection, fanpage care (inbox/comments), polling interval, last poll.
    2. TikTok: Account connection (PostPeer), publishing/brand kits, khong claim inbox.
    3. Instagram & YouTube: Trang thai 'Chua ho tro', publish_supported = False, khong bia so lieu.
    """
    res = client.get("/ops/channels/status")
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True

    # 1. Facebook connector capabilities
    fb = data.get("facebook")
    assert fb is not None
    assert "connected" in fb
    assert "pages" in fb
    assert isinstance(fb["pages"], list)
    assert "fanpage_care_enabled" in fb
    assert "poll_interval_seconds" in fb
    assert "last_poll" in fb
    assert "permissions" in fb
    # Facebook pages must have real id and name
    for page in fb["pages"]:
        assert "id" in page
        assert "name" in page

    # 2. TikTok connector capabilities
    tt = data.get("tiktok")
    assert tt is not None
    assert "connected" in tt
    assert "accounts" in tt
    assert isinstance(tt["accounts"], list)
    assert "masked_key" in tt
    assert "kits" in tt
    assert isinstance(tt["kits"], list)
    assert "recent_posts" in tt
    assert isinstance(tt["recent_posts"], list)
    # PostPeer chi ho tro publishing/brand kit, khong ho tro inbox
    assert "inbox_supported" not in tt or tt.get("inbox_supported") is False

    # 3. Instagram & YouTube capabilities (chua ho tro)
    others = {ch["id"]: ch for ch in data.get("other_channels", [])}
    assert "instagram" in others
    assert "youtube" in others

    insta = others["instagram"]
    assert insta["connected"] is False
    assert insta["publish_supported"] is False
    assert "chưa" in insta["statusLabel"].lower() or "chưa" in insta["note"].lower()

    yt = others["youtube"]
    assert yt["connected"] is False
    assert yt["publish_supported"] is False
    assert "chưa" in yt["statusLabel"].lower() or "chưa" in yt["note"].lower()


def test_direct_facebook_status_api(client):
    """Kiem tra truc tiep /connect/facebook/status"""
    res = client.get("/connect/facebook/status")
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert "connected" in data
    assert "fanpage_care_enabled" in data


def test_direct_tiktok_status_api(client):
    """Kiem tra truc tiep /tiktok/status"""
    res = client.get("/tiktok/status")
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert "connected" in data
    assert "accounts" in data
    assert "recent_posts" in data
