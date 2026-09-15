"""Test PR 8: complete_json grounded cho ambiguous comments và cấm CLI providers.

Chạy:
    pytest tests/python/test_aux_complete_json.py
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch

import aux_engine
from fanpage_care_ground import build_care_llm_prompt


@pytest.mark.anyio
async def test_complete_json_banned_patterns():
    """Prompt chứa fb_page_album, CLAUDE.md, pancake hoặc token EAA phải bị từ chối ngay lập tức."""
    # 1. Chứa fb_page_album
    res1 = await aux_engine.complete_json(
        system="Bắt buộc gọi tool fb_page_album để đăng ảnh",
        user="Chào bạn",
    )
    assert res1["refuse"] is True
    assert "fb_page_album" in res1["error"]

    # 2. Chứa CLAUDE.md
    res2 = await aux_engine.complete_json(
        system="Theo quy ước trong CLAUDE.md...",
        user="Hỏi học phí",
    )
    assert res2["refuse"] is True
    assert "CLAUDE.md" in res2["error"]

    # 3. Chứa pancake
    res3 = await aux_engine.complete_json(
        system="Bạn là trợ lý",
        user="Dùng pancake quản lý nhé",
    )
    assert res3["refuse"] is True
    assert "pancake" in res3["error"]

    # 4. Chứa token Meta EAA
    res4 = await aux_engine.complete_json(
        system="Trợ lý",
        user="Token của tôi là EAAB123456789xyz",
    )
    assert res4["refuse"] is True
    assert "EAA" in res4["error"]


@pytest.mark.anyio
async def test_complete_json_cli_provider_refuse_without_key():
    """Khi cấu hình provider CLI (anthropic-cli, codex...) mà không có API key fallback -> refuse."""
    settings = {
        "model": {
            "auxiliary": {"provider": "anthropic-cli", "model": "haiku"}
        }
    }
    res = await aux_engine.complete_json(
        system="Bạn là trợ lý",
        user="Hỏi thông tin",
        settings=settings,
    )
    assert res["refuse"] is True
    assert "CLI" in res["error"]


@pytest.mark.anyio
async def test_complete_json_cli_provider_fallback_to_api():
    """Khi cấu hình provider CLI nhưng có API key cho openrouter -> fallback sang openrouter."""
    settings = {
        "model": {
            "auxiliary": {"provider": "anthropic-cli", "model": "haiku"},
            "openrouter_key": "sk-or-test-key",
        }
    }

    mock_resp = json.dumps({
        "reply": "Dạ khóa tin học văn phòng học tại cơ sở Florita Quận 7 ạ.",
        "refuse": False,
        "cite_files": ["trung-tam-tin-hoc-sao-viet-quan-7-tphcm.md"],
    })

    async def _mock_stream(*args, **kwargs):
        yield {"type": "text", "content": mock_resp}

    with patch("engine.openrouter_stream", side_effect=_mock_stream):
        res = await aux_engine.complete_json(
            system="Bạn là trợ lý",
            user="Hỏi lớp Q7",
            settings=settings,
            tools=[{"name": "some_tool"}],  # tools phải bị ép thành []
        )
        assert res["refuse"] is False
        assert "Florita Quận 7" in res["reply"]
        assert res["cite_files"] == ["trung-tam-tin-hoc-sao-viet-quan-7-tphcm.md"]


@pytest.mark.anyio
async def test_complete_json_ungrounded_refuses():
    """Nếu model trả lời nhưng cite_files rỗng -> không grounded -> refuse."""
    settings = {
        "model": {
            "auxiliary": {"provider": "openrouter", "model": "test"},
            "openrouter_key": "sk-test",
        }
    }

    mock_resp = json.dumps({
        "reply": "Dạ học phí là 5 triệu đồng.",
        "refuse": False,
        "cite_files": [],  # Không trích dẫn file
    })

    async def _mock_stream(*args, **kwargs):
        yield {"type": "text", "content": mock_resp}

    with patch("engine.openrouter_stream", side_effect=_mock_stream):
        res = await aux_engine.complete_json(
            system="Bạn là trợ lý",
            user="Hỏi giá",
            settings=settings,
        )
        assert res["refuse"] is True
        assert "cite_files" in res["error"].lower()


@pytest.mark.anyio
async def test_complete_json_model_refuses():
    """Nếu model chủ động trả refuse: true -> trả refuse."""
    settings = {
        "model": {
            "auxiliary": {"provider": "openrouter", "model": "test"},
            "openrouter_key": "sk-test",
        }
    }

    mock_resp = json.dumps({
        "reply": "",
        "refuse": True,
        "cite_files": [],
    })

    async def _mock_stream(*args, **kwargs):
        yield {"type": "text", "content": mock_resp}

    with patch("engine.openrouter_stream", side_effect=_mock_stream):
        res = await aux_engine.complete_json(
            system="Bạn là trợ lý",
            user="Hỏi điều không có trong tài liệu",
            settings=settings,
        )
        assert res["refuse"] is True
        assert res["reply"] == ""


@pytest.mark.anyio
async def test_complete_json_timeout():
    """Khi model xử lý vượt quá timeout_s -> trả refuse do timeout."""
    settings = {
        "model": {
            "auxiliary": {"provider": "openrouter", "model": "test"},
            "openrouter_key": "sk-test",
        }
    }

    async def _mock_slow_stream(*args, **kwargs):
        await asyncio.sleep(0.5)
        yield {"type": "text", "content": "{}"}

    with patch("engine.openrouter_stream", side_effect=_mock_slow_stream):
        res = await aux_engine.complete_json(
            system="Bạn là trợ lý",
            user="Hỏi chậm",
            settings=settings,
            timeout_s=0.1,
        )
        assert res["refuse"] is True
        assert "timeout" in res["error"].lower()


def test_build_care_llm_prompt():
    """Kiểm tra build_care_llm_prompt không bao giờ để lộ token, không chứa CLAUDE.md và có định dạng chuẩn."""
    kit = {
        "name": "Trung Tâm Tin Học Sao Việt Quận 7",
        "file": "trung-tam-tin-hoc-sao-viet-quan-7-tphcm.md",
        "hotline": "0935 195 118",
        "address": "Chung cư Florita, D1, KDC Him Lam, Tân Hưng, Quận 7",
        "access_token": "EAABsecret_token_12345",
        "md": "Thông tin cơ sở Quận 7 có token EAAXYZ123456 ở đây.",
    }

    sys_p, user_p = build_care_llm_prompt(
        "108426965133947",
        kit,
        "Cho mình hỏi có lớp buổi tối không?",
        thread_comments=[{"from_name": "Nguyen A", "message": "Em muốn hỏi lịch"}],
    )

    # Tuyệt đối không chứa token
    assert "EAABsecret_token_12345" not in sys_p
    assert "EAAXYZ123456" not in sys_p
    assert "EAA" not in sys_p
    # Không chứa file hệ thống
    assert "CLAUDE.md" not in sys_p
    assert "fb_page_album" not in sys_p

    # Chứa hướng dẫn định dạng JSON
    assert '"cite_files"' in sys_p
    assert '"refuse"' in sys_p

    # User prompt chứa comment
    assert "Cho mình hỏi có lớp buổi tối không?" in user_p
    assert "Nguyen A" in user_p
