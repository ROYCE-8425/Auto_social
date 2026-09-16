"""Landing công khai `/` và `/chao`; console chủ máy ở `/app`."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client():
    with TestClient(main.app, base_url="http://127.0.0.1") as c:
        yield c


def test_root_is_landing(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Sao Việt Ops" in r.text
    assert "Não AI phía sau" in r.text
    assert "/ops" in r.text
    assert "/app" in r.text


def test_chao_same_landing(client):
    r = client.get("/chao")
    assert r.status_code == 200
    assert "Sao Việt Ops" in r.text


def test_app_is_javis_console(client):
    r = client.get("/app")
    assert r.status_code == 200
    assert "Javis OS" in r.text or "cview" in r.text or "alpine" in r.text.lower()


def test_website_file_exists():
    p = Path(__file__).resolve().parents[2] / "website" / "index.html"
    assert p.is_file()
    t = p.read_text(encoding="utf-8")
    assert "Be Vietnam Pro" in t
    assert "Javis OS" in t or "Javis" in t
