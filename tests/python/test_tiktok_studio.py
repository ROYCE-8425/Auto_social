# ============================================================
# Unit & Integration Tests: TikTok Carousel Studio & RBAC
# docs/dev/2026-09-17-gemini-tiktok-dang-that-ui.md
# ============================================================
import pytest
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))

import main
import ops_rbac
import tiktok_service
import config as cfgmod


@pytest.fixture
def test_env(monkeypatch):
    tmp_dir = Path(tempfile.mkdtemp(prefix="test_tiktok_studio_"))
    users_file = tmp_dir / "ops_users.json"
    sess_file = tmp_dir / "ops_sessions.json"

    # Setup fake vault
    vault = tmp_dir / "Brain Default"
    xuat_dir = vault / "attachments" / "dataset" / "_xuat-tiktok" / "bsn"
    xuat_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample 9:16 test image
    img = Image.new("RGB", (1080, 1920), color=(255, 0, 128))
    test_img_path = xuat_dir / "test_photo_1.png"
    img.save(test_img_path)

    # Create brand kits folder
    kits_dir = vault / "wiki" / "brand-kits"
    kits_dir.mkdir(parents=True, exist_ok=True)
    (kits_dir / "game-gia-re-bsn.md").write_text(
        "# Brand Kit: Game Giá Rẻ BSN\n\n"
        "- Tên thương hiệu: Game Giá Rẻ BSN\n\n"
        "## Kênh TikTok\n"
        "- Bật: true\n"
        "- accountId: 6aa3ba9df4c58f3c57921507\n"
        "- username: @seotrum\n"
        "- Tỷ lệ: 9:16\n"
        "- Caption: ngắn (8–18 dòng)\n"
        "- Hashtag: #GameGiaReBSN #SteamOffline\n"
        "- Tắt Duet: true\n"
        "- Tắt Stitch: true\n",
        encoding="utf-8"
    )

    # Create loop file
    javis_dir = vault / "Javis"
    javis_dir.mkdir(parents=True, exist_ok=True)
    (javis_dir / "dang-video-tiktok-hang-ngay.md").write_text(
        "---\n"
        "enabled: false\n"
        "cron: '0 11 * * *'\n"
        "---\n"
        "# Đăng video TikTok hàng ngày\n",
        encoding="utf-8"
    )

    monkeypatch.setattr(ops_rbac, "OPS_USERS_FILE", users_file)
    monkeypatch.setattr(ops_rbac, "OPS_SESSIONS_FILE", sess_file)
    monkeypatch.setattr(ops_rbac, "_OPS_SESSIONS", {})
    monkeypatch.setattr(main, "_brain_root", lambda b: str(vault))
    monkeypatch.setattr(tiktok_service, "_get_vault_root", lambda v: vault)

    with TestClient(main.app, base_url="http://127.0.0.1") as c:
        yield c, vault, tmp_dir

    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_serve_tiktok_media_valid(test_env):
    """GET /tiktok-media/... phục vụ ảnh công khai hợp lệ từ _xuat-tiktok."""
    c, vault, _ = test_env
    resp = c.get("/tiktok-media/bsn/test_photo_1.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert len(resp.content) > 0


def test_serve_tiktok_media_path_traversal_blocked(test_env):
    """GET /tiktok-media/... chặn dứt khoát mọi nỗ lực path traversal (404)."""
    c, vault, _ = test_env
    
    # Attempt to read outside _xuat-tiktok
    secret_file = vault / "secret.txt"
    secret_file.write_text("SUPER_SECRET_KEY")

    traversal_paths = [
        "/tiktok-media/../secret.txt",
        "/tiktok-media/../../secret.txt",
        "/tiktok-media/..%2f..%2fsecret.txt",
        "/tiktok-media/bsn/../../secret.txt",
        "/tiktok-media/non_existent.png",
    ]
    for p in traversal_paths:
        resp = c.get(p)
        assert resp.status_code in (404, 401, 400), f"Path traversal not blocked for: {p}"
        assert "SUPER_SECRET_KEY" not in resp.text


def test_tiktok_status_returns_masked_key_and_loop(test_env, monkeypatch):
    """GET /tiktok/status trả về masked key (...xxxx) và loop disabled."""
    c, vault, _ = test_env

    # Login as owner/staff
    ops_rbac.create_user("owner_status_chk", "statuspass123", role="owner", name="Chủ Máy")
    login_res = c.post("/ops/auth/login", json={"username": "owner_status_chk", "password": "statuspass123"})
    cookies = login_res.cookies

    # Mock connection with fake key
    monkeypatch.setattr(tiktok_service, "get_postpeer_connection", lambda: {
        "enabled": True,
        "masked_key": "...8888",
        "api_key": "actual_secret_key_12345678888",
        "perm": "full"
    })

    resp = c.get("/tiktok/status", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["connected"] is True
    assert data["masked_key"] == "...8888"
    assert "actual_secret_key" not in json.dumps(data)
    assert data["loop"]["enabled"] is False
    assert len(data["kits"]) >= 1
    assert data["kits"][0]["username"] == "@seotrum"


def test_rbac_staff_forbidden_from_posting(test_env):
    """Staff nhận 403 Forbidden khi cố gọi POST /tiktok/post hoặc /tiktok/upload."""
    c, vault, _ = test_env

    # Create staff user and login
    ops_rbac.create_user("nhanvien_tiktok", "staff123", role="staff", name="Nhân Viên")
    login_res = c.post("/ops/auth/login", json={"username": "nhanvien_tiktok", "password": "staff123"})
    assert login_res.status_code == 200
    cookies = login_res.cookies

    # Staff CAN view status
    res_status = c.get("/tiktok/status", cookies=cookies)
    assert res_status.status_code == 200

    # Staff FORBIDDEN on POST /tiktok/post (403)
    res_post = c.post("/tiktok/post", json={"brand_kit": "game-gia-re-bsn"}, cookies=cookies)
    assert res_post.status_code == 403
    assert "Chỉ chủ máy" in res_post.json()["error"] or "không có quyền" in res_post.json()["error"]

    # Staff FORBIDDEN on POST /tiktok/loop-toggle (403)
    res_loop = c.post("/tiktok/loop-toggle", json={"enabled": True}, cookies=cookies)
    assert res_loop.status_code == 403

    # Staff FORBIDDEN on POST /tiktok/kit-account (403)
    res_kit = c.post("/tiktok/kit-account", json={"brand_kit": "game-gia-re-bsn", "account_id": "123"}, cookies=cookies)
    assert res_kit.status_code == 403


def test_owner_can_toggle_loop_and_update_kit(test_env):
    """Owner có quyền đổi loop và cập nhật accountId của brand kit."""
    c, vault, _ = test_env

    # Create owner and login
    ops_rbac.create_user("chumay_tiktok", "ownerpass123", role="owner", name="Chủ Máy")
    login_res = c.post("/ops/auth/login", json={"username": "chumay_tiktok", "password": "ownerpass123"})
    assert login_res.status_code == 200
    cookies = login_res.cookies

    # 1. Toggle loop to True
    res_loop_on = c.post("/tiktok/loop-toggle", json={"enabled": True}, cookies=cookies)
    assert res_loop_on.status_code == 200
    assert res_loop_on.json()["loop"]["enabled"] is True

    # Check that file was updated
    loop_file = vault / "Javis" / "dang-video-tiktok-hang-ngay.md"
    assert "enabled: true" in loop_file.read_text(encoding="utf-8")

    # 2. Toggle loop back to False (default safe)
    res_loop_off = c.post("/tiktok/loop-toggle", json={"enabled": False}, cookies=cookies)
    assert res_loop_off.status_code == 200
    assert res_loop_off.json()["loop"]["enabled"] is False
    assert "enabled: false" in loop_file.read_text(encoding="utf-8")

    # 3. Update kit accountId
    res_kit = c.post("/tiktok/kit-account", json={
        "brand_kit": "game-gia-re-bsn",
        "account_id": "new_acc_999",
        "account_name": "@new_seotrum"
    }, cookies=cookies)
    assert res_kit.status_code == 200
    kit_content = (vault / "wiki" / "brand-kits" / "game-gia-re-bsn.md").read_text(encoding="utf-8")
    assert "- accountId: new_acc_999" in kit_content


def test_owner_post_photos_mock_postpeer_logs_jsonl(test_env, monkeypatch):
    """Owner đăng carousel -> gọi PostPeer với autoAddMusic=true -> ghi log vào Javis/tiktok-posts.jsonl."""
    c, vault, _ = test_env

    # Login as owner
    ops_rbac.create_user("owner_post", "owner12345", role="owner", name="Chủ Máy")
    login_res = c.post("/ops/auth/login", json={"username": "owner_post", "password": "owner12345"})
    cookies = login_res.cookies

    # Mock PostPeer HTTP POST response
    import requests
    class MockResponse:
        status_code = 200
        ok = True
        def json(self):
            return {
                "id": "postpeer_post_xyz789",
                "status": "published",
                "url": "https://www.tiktok.com/@seotrum/video/789123456"
            }
    
    called_payloads = []
    def fake_post(url, headers=None, json=None, timeout=None):
        called_payloads.append({"url": url, "json": json})
        return MockResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(tiktok_service, "get_postpeer_token", lambda: "fake_key_9999")
    monkeypatch.setattr(tiktok_service, "get_postpeer_connection", lambda: {
        "enabled": True,
        "masked_key": "...9999",
        "api_key": "fake_key_9999",
        "perm": "full"
    })

    res = c.post("/tiktok/post", json={
        "brand_kit": "game-gia-re-bsn",
        "product_title": "The Blood of Dawnwalker",
        "product_price": "45.000 ₫",
        "auto_add_music": True
    }, cookies=cookies)

    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["postpeer_id"] == "postpeer_post_xyz789"
    assert data["tiktok_url"] == "https://www.tiktok.com/@seotrum/video/789123456"

    # Verify PostPeer was called with autoAddMusic: True and https:// media URLs
    assert len(called_payloads) == 1
    sent_json = called_payloads[0]["json"]
    assert sent_json["autoAddMusic"] is True
    assert sent_json["accountId"] == "6aa3ba9df4c58f3c57921507"
    assert len(sent_json["urls"]) >= 1
    for u in sent_json["urls"]:
        assert u.startswith("https://trannhuy.online/tiktok-media/")

    # Verify Javis/tiktok-posts.jsonl contains the new post
    log_file = vault / "Javis" / "tiktok-posts.jsonl"
    assert log_file.is_file()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    log_entry = json.loads(lines[0])
    assert log_entry["postpeer_id"] == "postpeer_post_xyz789"
    assert log_entry["auto_add_music"] is True
    assert log_entry["brand"] == "bsn"


def test_crop_image_to_9_16(tmp_path):
    """Kiểm tra hàm crop_image_to_9_16 cắt ảnh ngang thành ảnh 9:16 dọc 1080x1920 không méo."""
    src = tmp_path / "horizontal.jpg"
    # Create 1920x1080 (16:9 horizontal)
    im = Image.new("RGB", (1920, 1080), color=(10, 20, 30))
    im.save(src)

    out = tiktok_service.crop_image_to_9_16(src)
    assert out.is_file()
    with Image.open(out) as cropped:
        w, h = cropped.size
        # Ratio should be 9:16 (target width: 1080, target height: 1920)
        assert w == 1080
        assert h == 1920
