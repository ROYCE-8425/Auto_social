"""Test suite cho PR 10: Messenger runtime, 24h window, và Human Takeover."""
import time
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

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

        courses_dir = vault_dir / "wiki" / "courses"
        courses_dir.mkdir(parents=True)
        tin_hoc = courses_dir / "tin-hoc-van-phong.md"
        tin_hoc.write_text(
            """# Khóa học Tin học văn phòng
- Học phí: 1.200.000 VNĐ
- Thời lượng: 12 buổi
""",
            encoding="utf-8",
        )

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(store, "DEFAULT_DB_PATH", state_dir / "fanpage_care.sqlite3")
        monkeypatch.setattr(fanpage_care_graph, "STATE_DIR", state_dir)

        yield td


@pytest.mark.anyio
async def test_human_echo_triggers_takeover(monkeypatch):
    """Echo từ nhân viên (không có metadata care-worker) phải kích hoạt 4h takeover."""
    store.init_db()
    pid = "108426965133947"
    psid = "user_psid_12345"

    mock_settings = {
        "fanpage_care": {
            "enabled": True,
            "mode": "suggest",
            "brain": "Brain Default",
            "takeover_hours": 4.0,
            "pages": {pid: {"mode": "suggest"}},
        }
    }
    monkeypatch.setattr(config, "read_settings", lambda: mock_settings)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    feat = fanpage_care.register(app, deps)

    # 1. Ban đầu: chưa bị takeover
    assert not store.is_under_takeover(pid, psid)

    # 2. Nhân viên trả lời qua Meta Business Suite (echo, sender=pid, recipient=psid, metadata="")
    echo_item = {
        "sender": {"id": pid},
        "recipient": {"id": psid},
        "timestamp": int(time.time() * 1000),
        "message": {
            "mid": "m_echo_001",
            "is_echo": True,
            "text": "Chào bạn, mình là nhân viên tư vấn đây ạ!",
            "metadata": "",
        },
    }

    res = await feat.process_inbound_message(pid, echo_item)
    assert res["takeover_activated"] is True
    assert store.is_under_takeover(pid, psid) is True

    # Kiểm tra hạn takeover: khoảng 4h
    w = store.get_messaging_window(pid, psid)
    assert w is not None
    assert w["takeover_until"] > time.time() + 3.5 * 3600

    # 3. Khách hàng gửi tin nhắn đến trong khi đang takeover -> bot bỏ qua, không tạo draft hay reply
    user_msg_item = {
        "sender": {"id": psid},
        "recipient": {"id": pid},
        "timestamp": int(time.time() * 1000),
        "message": {
            "mid": "m_user_001",
            "text": "Học phí tin học văn phòng bao nhiêu ạ?",
        },
    }
    res_inbound = await feat.process_inbound_message(pid, user_msg_item)
    assert res_inbound["replied"] is False
    assert res_inbound["draft_created"] is False
    assert len(store.list_drafts()) == 0


@pytest.mark.anyio
async def test_care_worker_echo_does_not_trigger_takeover(monkeypatch):
    """Echo do chính Javis gửi (metadata='care-worker') không kích hoạt takeover."""
    store.init_db()
    pid = "108426965133947"
    psid = "user_psid_67890"

    mock_settings = {
        "fanpage_care": {
            "enabled": True,
            "mode": "full",
            "brain": "Brain Default",
            "takeover_hours": 4.0,
            "pages": {pid: {"mode": "full"}},
        }
    }
    monkeypatch.setattr(config, "read_settings", lambda: mock_settings)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    feat = fanpage_care.register(app, deps)

    echo_item = {
        "sender": {"id": pid},
        "recipient": {"id": psid},
        "timestamp": int(time.time() * 1000),
        "message": {
            "mid": "m_echo_care_001",
            "is_echo": True,
            "text": "Dạ học phí là 1.200.000đ ạ!",
            "metadata": "care-worker",
        },
    }

    res = await feat.process_inbound_message(pid, echo_item)
    assert res["takeover_activated"] is False
    assert store.is_under_takeover(pid, psid) is False


@pytest.mark.anyio
async def test_release_human_takeover_api(monkeypatch):
    """Endpoint POST /fanpage-care/conversations/release-takeover gỡ bỏ lệnh takeover để Javis nhận lại."""
    store.init_db()
    pid = "108426965133947"
    psid = "user_psid_release"

    mock_settings = {
        "fanpage_care": {
            "enabled": True,
            "mode": "suggest",
            "brain": "Brain Default",
        }
    }
    monkeypatch.setattr(config, "read_settings", lambda: mock_settings)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    feat = fanpage_care.register(app, deps)
    client = TestClient(app)

    # Đặt takeover nhân viên
    store.set_human_takeover(pid, psid, duration_hours=4.0)
    assert store.is_under_takeover(pid, psid) is True

    # Gọi API release takeover
    resp = client.post("/fanpage-care/conversations/release-takeover", json={"page_id": pid, "psid": psid})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["takeover_until"] == 0.0

    # Kiểm tra store
    assert store.is_under_takeover(pid, psid) is False

    # Tin nhắn khách hàng tiếp theo sẽ được bot xử lý bình thường (tạo draft ở mode suggest)
    user_msg_item = {
        "sender": {"id": psid},
        "recipient": {"id": pid},
        "timestamp": int(time.time() * 1000),
        "message": {
            "mid": "m_user_after_release",
            "text": "Cho mình xin lịch học tuần này với",
        },
    }
    res_inbound = await feat.process_inbound_message(pid, user_msg_item)
    assert res_inbound["draft_created"] is True
    drafts = store.list_drafts()
    assert len(drafts) == 1
    assert drafts[0]["target_id"] == psid


@pytest.mark.anyio
async def test_inbound_outside_24h_window(monkeypatch):
    """Tin nhắn ngoài cửa sổ 24h tạo draft với cảnh báo expired_window."""
    store.init_db()
    pid = "108426965133947"
    psid = "user_psid_expired"

    mock_settings = {
        "fanpage_care": {
            "enabled": True,
            "mode": "full",
            "brain": "Brain Default",
            "pages": {pid: {"mode": "full"}},
        }
    }
    monkeypatch.setattr(config, "read_settings", lambda: mock_settings)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    feat = fanpage_care.register(app, deps)

    # Giả lập cửa sổ 24h đã hết hạn bằng cách monkeypatch store.is_in_24h_window
    monkeypatch.setattr(store, "is_in_24h_window", lambda p, u: False)

    user_msg_item = {
        "sender": {"id": psid},
        "recipient": {"id": pid},
        "timestamp": int(time.time() * 1000),
        "message": {
            "mid": "m_user_expired",
            "text": "Alo còn lớp không ad?",
        },
    }

    res = await feat.process_inbound_message(pid, user_msg_item)
    assert res["draft_created"] is True
    assert res["replied"] is False

    drafts = store.list_drafts()
    assert len(drafts) == 1
    assert drafts[0]["class"] == "expired_window"
    assert "24 giờ" in drafts[0]["proposed"]


@pytest.mark.anyio
async def test_inbound_message_full_mode_reply(monkeypatch):
    """Mode full: tin nhắn FAQ hợp lệ trong cửa sổ 24h sẽ gọi fb_message_send tự động."""
    store.init_db()
    pid = "108426965133947"
    psid = "user_psid_full_reply"

    mock_settings = {
        "fanpage_care": {
            "enabled": True,
            "mode": "full",
            "brain": "Brain Default",
            "quiet_hours": "00-00",  # tắt quiet hours cho test
            "features": {"auto_reply_messenger": True},
            "pages": {pid: {"mode": "full"}},
        }
    }
    monkeypatch.setattr(config, "read_settings", lambda: mock_settings)

    mock_call = AsyncMock(return_value={"message_id": "mid_fb_send_success"})
    monkeypatch.setattr(fanpage_care_graph, "call", mock_call)

    app = FastAPI()
    deps = fanpage_care.FanpageCareDeps(vault_root=Path(config.STATE_DIR).parent / "vault")
    feat = fanpage_care.register(app, deps)

    user_msg_item = {
        "sender": {"id": psid},
        "recipient": {"id": pid},
        "timestamp": int(time.time() * 1000),
        "message": {
            "mid": "m_user_faq_01",
            "text": "Học phí khóa tin học văn phòng Florita Quận 7 là bao nhiêu ạ?",
        },
    }

    res = await feat.process_inbound_message(pid, user_msg_item)
    assert res["replied"] is True
    assert mock_call.called
    call_args = mock_call.call_args[0]
    assert call_args[0] == "fb_message_send"
    assert call_args[1]["recipient_id"] == psid
    assert call_args[1]["page_id"] == pid
    assert "0935 195 118" in call_args[1]["message"] or "Tin Học Sao Việt" in call_args[1]["message"]

    # Kiểm tra store đã cập nhật window
    assert store.is_in_24h_window(pid, psid) is True
