"""Test suite cho PR 7: Webhook /hook/facebook cho bình luận."""
import hashlib
import hmac
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import config
import fanpage_care
import fanpage_care_graph
import fanpage_care_store as store
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        vault_dir = p / "vault"
        vault_dir.mkdir(parents=True)
        kits_dir = vault_dir / "wiki" / "brand-kits"
        kits_dir.mkdir(parents=True)

        q7_kit = kits_dir / "trung-tam-tin-hoc-sao-viet-quan-7.md"
        q7_kit.write_text(
            """# Trung Tâm Tin Học Sao Việt Quận 7
- Page ID: 108426965133947
- Tên Fanpage: Trung Tâm Tin Học Sao Việt Quận 7
- Cơ sở / địa chỉ: Florita, Quận 7
- Hotline: 0935 195 118
""",
            encoding="utf-8",
        )

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(store, "DEFAULT_DB_PATH", state_dir / "fanpage_care.sqlite3")
        monkeypatch.setattr(fanpage_care_graph, "STATE_DIR", state_dir)

        yield td


def test_webhook_verify_challenge(monkeypatch):
    """GET /hook/facebook xác thực challenge của Meta."""
    mock_settings = {
        "fanpage_care": {
            "enabled": True,
            "webhook_verify_token": "my_secret_verify_token_123",
        }
    }
    monkeypatch.setattr(config, "read_settings", lambda: mock_settings)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    feat = fanpage_care.register(app, deps)
    client = TestClient(app)

    # 1. Token đúng
    resp = client.get(
        "/hook/facebook?hub.mode=subscribe&hub.verify_token=my_secret_verify_token_123&hub.challenge=test_challenge_abc"
    )
    assert resp.status_code == 200
    assert resp.text == "test_challenge_abc"

    # 2. Token sai -> 403
    resp_bad = client.get(
        "/hook/facebook?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=test_challenge_abc"
    )
    assert resp_bad.status_code == 403

    # 3. Sai mode -> 403
    resp_mode = client.get(
        "/hook/facebook?hub.mode=unsubscribe&hub.verify_token=my_secret_verify_token_123&hub.challenge=test"
    )
    assert resp_mode.status_code == 403


@pytest.mark.anyio
async def test_webhook_hmac_and_events(monkeypatch):
    """POST /hook/facebook kiểm tra chữ ký HMAC và nuốt sự kiện comment/reply."""
    app_secret = "meta_app_secret_xyz789"

    mock_settings = {
        "fanpage_care": {
            "enabled": True,
            "mode": "suggest",
            "brain": "Brain Default",
            "app_secret": app_secret,
        }
    }
    monkeypatch.setattr(config, "read_settings", lambda: mock_settings)

    store.init_db()

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    feat = fanpage_care.register(app, deps)
    client = TestClient(app)

    payload_add = {
        "object": "page",
        "entry": [
            {
                "id": "108426965133947",
                "time": 1700000000,
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "verb": "add",
                            "comment_id": "wh_c_101",
                            "post_id": "108426965133947_post1",
                            "from": {"id": "user_fb_99", "name": "Hoàng Khách"},
                            "message": "Cho em hỏi lịch học Word tối",
                            "created_time": 1700000000,
                        },
                    }
                ],
            }
        ],
    }

    raw_body = json.dumps(payload_add).encode("utf-8")
    valid_sig = "sha256=" + hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # 1. Chữ ký sai -> 403
    resp_bad = client.post(
        "/hook/facebook",
        content=raw_body,
        headers={"X-Hub-Signature-256": "sha256=bad_hex", "Content-Type": "application/json"},
    )
    assert resp_bad.status_code == 403

    # 2. Chữ ký đúng -> 200 OK
    resp_ok = client.post(
        "/hook/facebook",
        content=raw_body,
        headers={"X-Hub-Signature-256": valid_sig, "Content-Type": "application/json"},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json().get("status") == "ok"

    # Chạy background processing
    await feat.process_webhook_payload(payload_add)

    # Kiểm tra event được lưu vào database
    events = store.list_events(page_id="108426965133947")
    matching = [e for e in events if e["object_id"] == "wh_c_101"]
    assert len(matching) == 1
    assert matching[0]["body"] == "Cho em hỏi lịch học Word tối"
    assert matching[0]["class"] == "faq"

    # 3. Test verb=edited
    payload_edit = {
        "object": "page",
        "entry": [
            {
                "id": "108426965133947",
                "time": 1700000050,
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "verb": "edited",
                            "comment_id": "wh_c_101",
                            "post_id": "108426965133947_post1",
                            "from": {"id": "user_fb_99", "name": "Hoàng Khách Đã Sửa"},
                            "message": "Cho em hỏi lịch học Word tối và học phí ạ",
                            "created_time": 1700000050,
                        },
                    }
                ],
            }
        ],
    }

    await feat.process_webhook_payload(payload_edit)

    events_after = store.list_events(page_id="108426965133947")
    matching_after = [e for e in events_after if e["object_id"] == "wh_c_101"]
    assert len(matching_after) == 1
    assert matching_after[0]["body"] == "Cho em hỏi lịch học Word tối và học phí ạ"
    assert matching_after[0]["from_name"] == "Hoàng Khách Đã Sửa"
