from _paths import ROOT, SERVER
import pytest
from fastapi.testclient import TestClient

from main import app


def make_client():
    # Dùng base_url 127.0.0.1 để vượt qua kiểm tra csrf_decision
    return TestClient(app, base_url="http://127.0.0.1")


@pytest.fixture
def client():
    return make_client()


def test_facebook_status_endpoint(client):
    res = client.get("/connect/facebook/status")
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert "connected" in data
    assert "pages" in data
    assert isinstance(data["pages"], list)
    assert "permissions" in data
    assert "fanpage_care_enabled" in data
    assert "poll_interval_seconds" in data
    # Không được bịa số liệu hay crash
    for p in data["pages"]:
        assert "id" in p
        assert "name" in p


def test_ops_channels_status_endpoint(client):
    res = client.get("/ops/channels/status")
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert "facebook" in data
    assert "tiktok" in data
    assert "other_channels" in data
    
    # Kiểm tra kênh khác (Zalo, Instagram, Youtube) không bịa số liệu reach/order/post
    others = {ch["id"]: ch for ch in data["other_channels"]}
    assert "zalo" in others
    assert "instagram" in others
    assert "youtube" in others

    # Zalo không claim publish vì chỉ hỗ trợ chăm sóc tin nhắn qua Agent MCP
    assert others["zalo"]["publish_supported"] is False

    # Kênh mạng xã hội phản ánh trung thực kết nối qua PostPeer Gateway
    for ch_id in ("instagram", "youtube"):
        ch = others[ch_id]
        if ch.get("connected"):
            assert ch["publish_supported"] is True
            assert "kết nối" in ch["statusLabel"].lower()
        else:
            assert ch["publish_supported"] is False
            assert "chưa" in ch["statusLabel"].lower() or "chưa" in ch["note"].lower()


if __name__ == "__main__":
    c = make_client()
    test_facebook_status_endpoint(c)
    test_ops_channels_status_endpoint(c)
    print("OK - test_social_channels_status: tat ca pass")
