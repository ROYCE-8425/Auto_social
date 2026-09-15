"""Test suite kiểm tra endpoint /fanpage-care/state đọc quyền Facebook từ mcp_store."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import config
import fanpage_care
import fanpage_care_store as store
import mcp_store
import mcp_catalog
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        vault_dir = p / "vault"
        vault_dir.mkdir(parents=True)

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(store, "DEFAULT_DB_PATH", state_dir / "fanpage_care.sqlite3")
        store.init_db()

        yield td


def test_state_perm_empty_connections(monkeypatch):
    """Khi chưa có connection nào -> connected=False, perm=readonly."""
    monkeypatch.setattr(mcp_store, "list_connections", lambda: [])
    # Đảm bảo mcp_catalog.get_connection không được gọi
    if hasattr(mcp_catalog, "get_connection"):
        mock_cat = MagicMock()
        monkeypatch.setattr(mcp_catalog, "get_connection", mock_cat)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    fanpage_care.register(app, deps)
    client = TestClient(app)

    resp = client.get("/fanpage-care/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["facebook_connected"] is False
    assert data["connection_perm"] == "readonly"
    assert data["facebook_label"] == ""


def test_state_perm_full(monkeypatch):
    """Khi có connection facebook-pages enabled với perm=full -> connected=True, perm=full."""
    mock_conns = [
        {
            "id": "c_fb_1",
            "connector_id": "facebook-pages",
            "label": "Fanpage Chính",
            "enabled": True,
            "perm": "full",
        }
    ]
    monkeypatch.setattr(mcp_store, "list_connections", lambda: mock_conns)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    fanpage_care.register(app, deps)
    client = TestClient(app)

    resp = client.get("/fanpage-care/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["facebook_connected"] is True
    assert data["connection_perm"] == "full"
    assert "Fanpage Chính" in data["facebook_label"]


def test_state_perm_readonly(monkeypatch):
    """Khi có connection facebook-pages với perm=readonly -> connected=True, perm=readonly."""
    mock_conns = [
        {
            "id": "c_fb_2",
            "connector_id": "facebook-pages",
            "label": "Fanpage Chi Nhánh",
            "enabled": True,
            "perm": "readonly",
        }
    ]
    monkeypatch.setattr(mcp_store, "list_connections", lambda: mock_conns)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    fanpage_care.register(app, deps)
    client = TestClient(app)

    resp = client.get("/fanpage-care/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["facebook_connected"] is True
    assert data["connection_perm"] == "readonly"
