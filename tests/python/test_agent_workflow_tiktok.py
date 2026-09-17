"""Kiểm tra cấu trúc và tính hợp lệ của Agent, Workflow, Skill và Loop cho TikTok.

Quy chuẩn theo docs/dev/2026-09-17-gemini-agent-skill-workflow.md:
- Agent bien-tap-tiktok tồn tại, frontmatter type: agent, kỹ năng dang-carousel-tiktok.
- Workflow dang-tiktok-carousel tồn tại, frontmatter type: workflow, status: on, trỏ đúng agent.
- Skill dang-carousel-tiktok tồn tại, group TikTok, không có mock post_id.
- Skill soan-nhap-tuong-tac tồn tại, mỏng, chỉ phục vụ chat, cấm loop poller.
- Loop dang-video-tiktok-hang-ngay tồn tại, enabled: false.
- Cấm: Không tồn tại agent poller comment hay workflow trả lời tự động mọi comment.
- API /agents và /workflows trả về đúng danh mục.
"""
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
BRAIN = ROOT / "brains" / "Brain Default"


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def test_agent_bien_tap_tiktok_exists_and_valid():
    agent_file = BRAIN / "agents" / "bien-tap-tiktok.md"
    assert agent_file.is_file(), f"Thiếu file {agent_file}"
    meta = _read_frontmatter(agent_file)
    assert meta.get("type") == "agent"
    assert meta.get("slug") == "bien-tap-tiktok"
    assert "dang-carousel-tiktok" in (meta.get("skills") or [])
    
    content = agent_file.read_text(encoding="utf-8")
    assert "postpeer_tiktok_photos" in content
    assert "TUYỆT ĐỐI CẤM BỊA HOẶC MOCK" in content
    assert "TUYỆT ĐỐI CẤM GỌI CÁC TOOL FACEBOOK" in content


def test_workflow_dang_tiktok_carousel_exists_and_valid():
    wf_file = BRAIN / "workflows" / "dang-tiktok-carousel.md"
    assert wf_file.is_file(), f"Thiếu file {wf_file}"
    meta = _read_frontmatter(wf_file)
    assert meta.get("type") == "workflow"
    assert meta.get("slug") == "dang-tiktok-carousel"
    assert meta.get("status") in ("on", True, "active")
    
    steps = meta.get("steps") or []
    assert len(steps) >= 1
    assert steps[0].get("agent") == "bien-tap-tiktok"
    assert "postpeer_tiktok_photos" in steps[0].get("task", "")


def test_skill_dang_carousel_tiktok_exists():
    skill_file = BRAIN / "skills" / "dang-carousel-tiktok" / "SKILL.md"
    assert skill_file.is_file(), f"Thiếu file {skill_file}"
    meta = _read_frontmatter(skill_file)
    assert meta.get("group") == "TikTok"
    
    content = skill_file.read_text(encoding="utf-8")
    assert "postpeer_tiktok_photos" in content
    assert "auto_add_music" in content
    assert "https://trannhuy.online/tiktok-media/" in content
    assert "CẤM mock post_id" in content


def test_skill_soan_nhap_tuong_tac_is_thin_and_no_poller():
    skill_file = BRAIN / "skills" / "soan-nhap-tuong-tac" / "SKILL.md"
    assert skill_file.is_file(), f"Thiếu file {skill_file}"
    meta = _read_frontmatter(skill_file)
    assert meta.get("group") == "Content"
    
    content = skill_file.read_text(encoding="utf-8")
    # Phải có nguyên tắc xác nhận từ người dùng
    assert "xác nhận" in content.lower()
    # Cấm poller ngầm hay vòng lặp
    assert "CẤM tự tạo vòng lặp" in content
    assert "CẤM spawn worker" in content


def test_loop_tiktok_is_disabled():
    loop_file = BRAIN / "Javis" / "loops" / "dang-video-tiktok-hang-ngay.md"
    assert loop_file.is_file(), f"Thiếu file {loop_file}"
    meta = _read_frontmatter(loop_file)
    assert meta.get("enabled") is False, "Loop TikTok bắt buộc phải enabled: false"
    
    content = loop_file.read_text(encoding="utf-8")
    assert "postpeer_tiktok_photos" in content


def test_ban_comment_poller_agent():
    """Đảm bảo không có bất kỳ agent hay workflow nào chạy poller đọc comment định kỳ."""
    agents_dir = BRAIN / "agents"
    for f in agents_dir.glob("*.md"):
        meta = _read_frontmatter(f)
        slug = meta.get("slug", f.stem)
        assert slug not in ("cham-soc-fanpage", "poller-comment", "doc-comment-dinh-ky"), (
            f"Phát hiện agent cấm: {slug}"
        )
        content = f.read_text(encoding="utf-8").lower()
        assert "lặp đọc comment mỗi 5 phút" not in content


def test_server_agents_and_workflows_api():
    """Kiểm tra hàm agents_index và workflows_index từ server/main.py trả về cả Facebook và TikTok."""
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    from main import agents_index, workflows_index
    
    agents = agents_index("Brain Default")
    agent_slugs = [a["slug"] for a in agents]
    assert "bien-tap-facebook" in agent_slugs
    assert "bien-tap-tiktok" in agent_slugs
    
    wfs = workflows_index("Brain Default")
    wf_slugs = [w["slug"] for w in wfs]
    assert "dang-bai-that-facebook" in wf_slugs
    assert "dang-tiktok-carousel" in wf_slugs


def test_tasks_tiktok_chua_dang_blocks_false_complete():
    """Kiểm tra Tasks._tiktok_chua_dang chặn không cho task đánh Hoàn thành nếu chưa đăng thật."""
    import sys
    sys.path.insert(0, str(ROOT / "server"))
    from tasks import TasksFeature
    
    task = {"title": "Soạn bài và đăng carousel lên kênh TikTok BSN", "route": "wf:dang-tiktok-carousel"}
    
    # 1. Bị thiếu API key hoặc chưa kết nối
    res_no_key = "Không đăng được vì PostPeer trong môi trường này chưa được kết nối: server trả lỗi thật Chưa kết nối PostPeer hoặc thiếu API key"
    err = TasksFeature._tiktok_chua_dang(task, res_no_key)
    assert "Chưa kết nối PostPeer" in err
    assert "Không đánh Hoàn thành" in err
    
    # 2. Bị mock post_id
    res_mock = "TIKTOK_POST_OK post_id=12345678 link=https://tiktok.com/@seotrum/video/12345678"
    err_mock = TasksFeature._tiktok_chua_dang(task, res_mock)
    assert "post_id giả lập" in err_mock
    
    # 3. Thành công thật
    res_ok = "TIKTOK_POST_OK post_id=67890abcdef123 link=https://www.tiktok.com/@seotrum/video/7391823719283 | BSN"
    err_ok = TasksFeature._tiktok_chua_dang(task, res_ok)
    assert err_ok == ""
