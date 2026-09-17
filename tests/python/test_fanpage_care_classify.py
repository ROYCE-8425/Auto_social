"""Test bộ phân loại Fanpage Care (0 token, pure Python).

Kiểm tra:
- Khớp 100% các trường hợp trong tests/fixtures/fanpage_care_classify_gold.json (>= 40 cases)
- Trích xuất và chuẩn hóa SĐT Việt Nam, chặn false positives (MST, Page ID)
- Luồng hội thoại cha - con (parent FAQ + child follow-up)
- Custom spam patterns
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "server"))

from fanpage_care_classify import (
    classify_comment,
    extract_vn_phones,
    normalize_vn_phone,
    fold_text,
)

_fails = []


def check(name: str, cond: bool, extra: str = ""):
    if cond:
        print(f"ok  {name}")
    else:
        print(f"FAIL {name} {extra}".rstrip())
        _fails.append(name)


# ---- 1. Test trích xuất SĐT VN ----
def test_phone_extraction():
    p1 = extract_vn_phones("gọi em số 0901.234.567 nhé")
    check("phone: 0901.234.567 chuẩn hóa", p1 == ["0901234567"], f"got: {p1}")

    p2 = extract_vn_phones("alo +84 935 195 118 tư vấn")
    check("phone: +84 935 195 118 chuẩn hóa", p2 == ["0935195118"], f"got: {p2}")

    p3 = extract_vn_phones("sdt 0935-195-118")
    check("phone: 0935-195-118 chuẩn hóa", p3 == ["0935195118"], f"got: {p3}")

    p_mst = extract_vn_phones("Công ty MST 3603708616 xuất hóa đơn")
    check("phone: MST 3603708616 không nhận là SĐT", p_mst == [], f"got: {p_mst}")

    p_pid = extract_vn_phones("Page ID: 108426965133947 cần hỗ trợ")
    check("phone: Page ID dài không nhận là SĐT", p_pid == [], f"got: {p_pid}")


# ---- 2. Test 46 test cases trong gold fixtures ----
def test_gold_fixtures():
    fixtures_path = ROOT / "tests" / "fixtures" / "fanpage_care_classify_gold.json"
    check("gold fixtures file tồn tại", fixtures_path.is_file())
    cases = json.loads(fixtures_path.read_text(encoding="utf-8"))
    check(f"gold fixtures có >= 40 cases ({len(cases)})", len(cases) >= 40)

    for case in cases:
        cid = case["id"]
        text = case["text"]
        page_id = case.get("page_id")
        from_id = case.get("from_id")
        is_reply = case.get("is_reply_to_page", False)

        res = classify_comment(
            text,
            page_id=page_id,
            from_id=from_id,
            is_reply_to_page=is_reply,
        )

        c_ok = res["class"] == case["expected_class"]
        f_ok = res["faq_intent"] == case["expected_faq_intent"]
        p_ok = res["phones"] == case["expected_phones"]

        check(
            f"gold {cid}: class={case['expected_class']}",
            c_ok,
            f"expected {case['expected_class']}, got {res['class']} (text='{text}') reasons={res.get('reasons')}",
        )
        if case["expected_faq_intent"]:
            check(
                f"gold {cid}: faq_intent={case['expected_faq_intent']}",
                f_ok,
                f"expected {case['expected_faq_intent']}, got {res['faq_intent']}",
            )
        check(
            f"gold {cid}: phones={case['expected_phones']}",
            p_ok,
            f"expected {case['expected_phones']}, got {res['phones']}",
        )


# ---- 3. Test kịch bản cha - con (parent FAQ + child follow-up) ----
def test_parent_child_conversation():
    # Khách 1 hỏi học phí
    parent_comment = "Khoá học này học phí bao nhiêu vậy ad?"
    r_parent = classify_comment(parent_comment, from_id="USER_A", page_id="PAGE_SV")
    check("parent: FAQ học phí", r_parent["class"] == "faq" and r_parent["faq_intent"] == "hoc_phi")

    # Khách 1 gửi tiếp SĐT sau khi page phản hồi
    child_comment = "Dạ gọi cho em số 0918.765.432 để tư vấn nhé"
    r_child = classify_comment(
        child_comment,
        from_id="USER_A",
        page_id="PAGE_SV",
        is_reply_to_page=True,
    )
    check(
        "child follow-up: lead có SĐT",
        r_child["class"] == "lead" and r_child["phones"] == ["0918765432"],
    )


# ---- 4. Test custom spam patterns ----
def test_custom_spam_patterns():
    custom_patterns = ["shopee.vn/deal-hot", "t.me/nhomkin"]
    res = classify_comment(
        "Xem đồ đẹp tại shopee.vn/deal-hot nha mọi người",
        spam_patterns=custom_patterns,
    )
    check("custom spam pattern khớp", res["class"] == "spam")


# ---- 5. Test Brand & Platform packs (Sao Việt FB, Sao Việt TT, Game Giá Rẻ BSN) ----
def test_brand_and_platform_packs():
    # 5a. Sao Việt FB: học phí Q7
    r_sv_fb = classify_comment("học phí Q7 bao nhiêu vậy ad?", platform="facebook", brand="saoviet")
    check("saoviet_fb: học phí Q7 -> hoc_phi", r_sv_fb["class"] == "faq" and r_sv_fb["faq_intent"] == "hoc_phi")
    check("saoviet_fb: brand=saoviet platform=facebook", r_sv_fb["brand"] == "saoviet" and r_sv_fb["platform"] == "facebook")

    # 5b. Sao Việt TT: ib bio / link bio
    r_sv_tt_bio = classify_comment("ib bio tư vấn em với", platform="tiktok", brand="saoviet")
    check("saoviet_tt: ib bio -> lead", r_sv_tt_bio["class"] == "lead")
    check("saoviet_tt: brand=saoviet platform=tiktok", r_sv_tt_bio["brand"] == "saoviet" and r_sv_tt_bio["platform"] == "tiktok")

    r_sv_tt_addr = classify_comment("địa chỉ học ở đâu ạ", platform="tiktok", brand="saoviet")
    check("saoviet_tt: địa chỉ học ở đâu -> dia_chi", r_sv_tt_addr["class"] == "faq" and r_sv_tt_addr["faq_intent"] == "dia_chi")
    check("saoviet_tt: reason chứa saoviet_tt:faq:dia_chi", "saoviet_tt:faq:dia_chi" in r_sv_tt_addr["reasons"])

    # 5c. Game Giá Rẻ BSN: Steam / Key / Bảo hành / Việt hóa
    r_bsn_bh = classify_comment("key steam bảo hành thế nào shop?", brand="bsn")
    check("bsn: key steam bảo hành -> bao_hanh", r_bsn_bh["class"] == "faq" and r_bsn_bh["faq_intent"] == "bao_hanh")
    check("bsn: brand=bsn", r_bsn_bh["brand"] == "bsn")
    check("bsn: không map khóa học Excel/MISA", "tin-hoc" not in r_bsn_bh["course_hints"] and "ke-toan" not in r_bsn_bh["course_hints"])

    r_bsn_buy = classify_comment("mình muốn mua key wukong", brand="game-gia-re-bsn")
    check("bsn: mua key -> lead", r_bsn_buy["class"] == "lead")
    check("bsn: slug game-gia-re-bsn nhận diện brand bsn", r_bsn_buy["brand"] == "bsn")

    r_bsn_ib = classify_comment("Check ib mình với ạ", brand="bsn")
    check("bsn: check ib -> lead (không học phí tin học)", r_bsn_ib["class"] == "lead")

    r_bsn_gia = classify_comment("giá cả sao q uy tín không ạ", brand="bsn")
    check("bsn: giá/uy tín -> gia_game", r_bsn_gia["class"] == "faq" and r_bsn_gia["faq_intent"] == "gia_game")

    r_bsn_vh = classify_comment("game này có việt hóa không shop", brand="bsn")
    check("bsn: việt hóa -> viet_hoa", r_bsn_vh["class"] == "faq" and r_bsn_vh["faq_intent"] == "viet_hoa")

    r_bsn_price = classify_comment("game wukong bao nhiêu shop", brand="bsn")
    check("bsn: giá game -> gia_game", r_bsn_price["class"] == "faq" and r_bsn_price["faq_intent"] == "gia_game")


def main():
    test_phone_extraction()
    test_gold_fixtures()
    test_parent_child_conversation()
    test_custom_spam_patterns()
    test_brand_and_platform_packs()

    if _fails:
        print(f"\nFAIL - {len(_fails)} test: {_fails}")
        sys.exit(1)
    print("\nOK - test_fanpage_care_classify: tất cả pass")


if __name__ == "__main__":
    main()

