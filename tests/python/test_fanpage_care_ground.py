"""Test suite cho server/fanpage_care_ground.py."""
import tempfile
from pathlib import Path
from fanpage_care_ground import (
    _fold,
    _one_line,
    address_short,
    get_course_fee,
    render_template,
    sanitize_kit,
)


def test_fold_and_one_line():
    assert _fold("Thủ Dầu Một - Bình Dương!") == "thudaumotbinhduong"
    assert _one_line("Dòng 1 | Dòng 2 \n Dòng 3") == "Dòng 1 Dòng 2 Dòng 3"
    assert "|" not in _one_line("Cơ sở 1 | Cơ sở 2")


def test_sanitize_kit():
    kit = {
        "name": "Sao Việt Q7",
        "access_token": "EAAxxxxxxxxxxxx",
        "notes": "Token EAA123456789 nằm ở đây",
    }
    clean = sanitize_kit(kit)
    assert "access_token" not in clean
    assert "EAA" not in clean["notes"]
    assert "[REDACTED_TOKEN]" in clean["notes"]


def test_address_short_single_campus():
    kit = {
        "name": "Trung Tâm Tin Học Sao Việt Quận 7",
        "address": "Phòng A1-02.04 Florita, Lô A1, KDC Him Lam, Tân Hưng, Quận 7, TP.HCM",
    }
    addr = address_short(kit)
    assert "Florita" in addr
    assert "|" not in addr


def test_address_short_multi_campus_matching():
    kit = {
        "name": "Trung Tâm Tin Học Sao Việt Thủ Dầu Một",
        "file": "trung-tam-tin-hoc-sao-viet-thu-dau-mot-binh-duong.md",
        "address": "Cơ sở Dĩ An: 184 Lê Hồng Phong | Cơ sở Thủ Dầu Một: 107 D5 KDC Phú Hoà | Cơ sở Tân Uyên: Tỉnh Lộ 746",
    }
    addr = address_short(kit)
    # Phải bắt đúng cơ sở Thủ Dầu Một, cấm gửi nhầm Dĩ An
    assert "Thủ Dầu Một" in addr or "107 D5" in addr
    assert "Lê Hồng Phong" not in addr
    assert "Tỉnh Lộ 746" not in addr
    assert "|" not in addr


def test_address_short_fail_closed_on_ambiguous():
    # Kit chung chung nhiều cơ sở không rõ chi nhánh -> trả ""
    kit = {
        "name": "Tin học Sao Việt Chung",
        "file": "tin-hoc-sao-viet-chung.md",
        "address": "Cơ sở 1: Hà Nội | Cơ sở 2: Đà Nẵng | Cơ sở 3: Cần Thơ",
    }
    addr = address_short(kit)
    assert addr == ""


def test_get_course_fee_no_fee_in_file():
    # Kit không có học phí -> trả None
    kit = {
        "name": "Sao Việt Q7",
        "md": "Trung tâm dạy tin học văn phòng, hotline 0935 195 118.",
    }
    assert get_course_fee("excel", kit) is None


def test_get_course_fee_with_exact_fee_in_file():
    # File có bảng giá cụ thể
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        courses_dir = root / "wiki" / "courses"
        courses_dir.mkdir(parents=True)
        cfile = courses_dir / "excel-van-phong.md"
        cfile.write_text(
            """# Khóa học Excel Văn Phòng
Bảng học phí theo cơ sở:
- Excel Quận 7: 3.500.000đ
- Excel Thủ Dầu Một: 3.200.000đ
- Excel Biên Hòa: 3.000.000đ
""",
            encoding="utf-8",
        )
        kit_q7 = {
            "name": "Sao Việt Quận 7",
            "file": "sao-viet-quan-7.md",
            "md": "Cơ sở Quận 7 Florita.",
        }
        fee_q7 = get_course_fee("excel", kit_q7, vault_root=root)
        assert fee_q7 == "3.500.000đ"

        kit_tdm = {
            "name": "Sao Việt Thủ Dầu Một",
            "file": "sao-viet-thu-dau-mot.md",
            "md": "Cơ sở Thủ Dầu Một Phú Hòa.",
        }
        fee_tdm = get_course_fee("excel", kit_tdm, vault_root=root)
        assert fee_tdm == "3.200.000đ"


def test_render_template_hoc_phi_without_fee_uses_hotline():
    # Khi KHÔNG có học phí trong file -> reply KHÔNG chứa số tiền (CẤM BỊA SỐ)
    kit = {
        "name": "Sao Việt Q7",
        "hotline": "0935 195 118",
        "md": "Cơ sở Florita Quận 7.",
    }
    reply = render_template("hoc_phi", kit, course_hint="Word")
    assert reply is not None
    assert "0935 195 118" in reply
    # Không chứa số tiền nào dạng 3.000.000 hay 500k
    import re
    # Bỏ số hotline ra trước khi kiểm tra số tiền
    no_hotline = reply.replace("0935 195 118", "").replace("0935195118", "")
    assert not re.search(r"\d{3,}", no_hotline)


def test_render_template_hoc_phi_with_fee():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        courses_dir = root / "wiki" / "courses"
        courses_dir.mkdir(parents=True)
        (courses_dir / "excel.md").write_text(
            "- Học phí Excel Quận 7: 3.500.000đ\n", encoding="utf-8"
        )
        kit = {
            "name": "Sao Việt Quận 7",
            "hotline": "0935 195 118",
            "file": "sao-viet-quan-7.md",
            "md": "Cơ sở Quận 7 Florita.",
        }
        reply = render_template("hoc_phi", kit, course_hint="Excel", vault_root=root)
        assert reply is not None
        assert "3.500.000đ" in reply
        assert "0935 195 118" in reply


def test_render_template_bsn_brand():
    kit = {
        "brand": "bsn",
        "name": "Game Giá Rẻ BSN",
        "hotline": "0877 104 996",
        "md": "## Care templates\n- ambiguous: \"Dạ shop đã gửi tin nhắn / hỗ trợ qua inbox rồi ạ, bạn check inbox hoặc liên hệ Hotline/Zalo {hotline} nhé ạ.\"",
    }
    reply = render_template("ambiguous", kit)
    assert reply is not None
    assert "0877 104 996" in reply
    assert "inbox" in reply.lower()

