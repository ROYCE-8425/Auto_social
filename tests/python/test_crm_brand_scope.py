# -*- coding: utf-8 -*-
"""Unit tests for CRM brand isolation, scope filtering, and backfill.

Tuân thủ docs/dev/2026-09-17-crm-loc-theo-brand.md:
1. Page BSN (343562028848465) -> brand=bsn, campus=Game Giá Rẻ BSN.
2. Page Sao Việt -> brand=saoviet, campus=Tin học Sao Việt.
3. Gộp: cùng người comment + IB cùng page -> 1 crm_id.
4. Cùng SĐT cùng brand -> 1 crm_id.
5. KHÔNG gộp khách BSN với học viên Sao Việt dù trùng SĐT.
6. search_customers(brand=...) lọc đúng theo brand/page.
7. backfill_customers_from_events quét events tạo hồ sơ còn thiếu.
8. RBAC cấm staff backfill.
"""
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "server"))

from server import fanpage_care_store as store
from server import ops_rbac


def test_customer_brand_resolution():
    assert store.resolve_brand("343562028848465") == "bsn"
    assert store.resolve_brand("988656934325292") == "saoviet"
    assert store.resolve_brand("any_page", "bsn") == "bsn"
    assert store.resolve_brand("any_page", "saoviet") == "saoviet"


def test_customer_creation_and_brand_isolation():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db_path = Path(td) / "care.db"

        # 1. Tạo khách BSN qua page BSN
        c_bsn, is_new1 = store.get_or_create_customer(
            name="Trần Như Ý",
            phones=["0912345678"],
            page_id="343562028848465",
            from_id="fb_user_bsn_1",
            campus="Game Giá Rẻ BSN",
            tag="game_acc",
            brand="bsn",
            db_path=db_path,
        )
        assert is_new1 is True
        assert c_bsn["brand"] == "bsn"
        assert "bsn" in c_bsn["tags"]

        # 2. Tạo khách Sao Việt có CÙNG SỐ ĐIỆN THOẠI
        c_sv, is_new2 = store.get_or_create_customer(
            name="Học Viên Như Ý",
            phones=["0912345678"],
            page_id="988656934325292",
            from_id="fb_user_sv_1",
            campus="Tin học Sao Việt Quận 7",
            tag="excel",
            brand="saoviet",
            db_path=db_path,
        )
        assert is_new2 is True
        assert c_sv["brand"] == "saoviet"
        assert "saoviet" in c_sv["tags"]

        # CRITICAL: KHÔNG ĐƯỢC GỘP BSN VÀ SAO VIỆT DÙ TRÙNG SĐT
        assert c_bsn["crm_id"] != c_sv["crm_id"]

        # 3. Khách thứ 2 của Sao Việt cùng SĐT -> PHẢI GỘP vào Sao Việt
        c_sv_merge, is_new3 = store.get_or_create_customer(
            name="Như Ý Tin Học",
            phones=["0912345678"],
            page_id="111222333444555",
            from_id="fb_user_sv_2",
            brand="saoviet",
            db_path=db_path,
        )
        assert is_new3 is False
        assert c_sv_merge["crm_id"] == c_sv["crm_id"]


def test_customer_dedup_comment_and_inbox_same_page():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db_path = Path(td) / "care.db"

        # Khách comment trên page BSN
        c1, is_new1 = store.get_or_create_customer(
            name="Game Thủ BSN",
            page_id="343562028848465",
            from_id="psid_999",
            brand="bsn",
            db_path=db_path,
        )
        assert is_new1 is True

        # Cùng người đó nhắn tin messenger trên page BSN (cùng psid/from_id)
        c2, is_new2 = store.get_or_create_customer(
            name="Game Thủ BSN",
            page_id="343562028848465",
            psid="psid_999",
            brand="bsn",
            db_path=db_path,
        )
        assert is_new2 is False
        assert c2["crm_id"] == c1["crm_id"]


def test_search_customers_brand_filtering():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db_path = Path(td) / "care.db"

        store.get_or_create_customer(
            name="Khách Mua Game BSN",
            page_id="343562028848465",
            from_id="u_bsn",
            brand="bsn",
            db_path=db_path,
        )
        store.get_or_create_customer(
            name="Học Viên Sao Việt",
            page_id="988656934325292",
            from_id="u_sv",
            brand="saoviet",
            db_path=db_path,
        )

        # 1. Tìm theo brand=bsn -> chỉ thấy khách BSN
        bsn_list = store.search_customers(brand="bsn", db_path=db_path)
        assert len(bsn_list) == 1
        assert bsn_list[0]["name"] == "Khách Mua Game BSN"
        assert bsn_list[0]["brand"] == "bsn"

        # 2. Tìm theo brand=saoviet -> chỉ thấy khách Sao Việt
        sv_list = store.search_customers(brand="saoviet", db_path=db_path)
        assert len(sv_list) == 1
        assert sv_list[0]["name"] == "Học Viên Sao Việt"
        assert sv_list[0]["brand"] == "saoviet"

        # 3. Tìm không truyền brand -> thấy tất cả
        all_list = store.search_customers(db_path=db_path)
        assert len(all_list) == 2

        # 4. Tìm theo page_id BSN
        page_bsn_list = store.search_customers(page_id="343562028848465", db_path=db_path)
        assert len(page_bsn_list) == 1
        assert page_bsn_list[0]["name"] == "Khách Mua Game BSN"


def test_backfill_customers_from_events():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db_path = Path(td) / "care.db"

        # Ghi một số events trước đó (chưa có trong bảng customers)
        now = time.time()
        store.record_event({
            "kind": "comment",
            "platform": "facebook",
            "page_id": "343562028848465",  # BSN page
            "object_id": "comment_bsn_1",
            "thread_id": "post_1",
            "from_id": "user_bsn_fb_1",
            "from_name": "Nguyễn Văn Game",
            "body": "Shop còn acc Steam GTA V không ạ? SĐT 0987654321",
            "class": "lead",
            "created_ts": now - 3600,
        }, db_path=db_path)

        store.record_event({
            "kind": "message",
            "platform": "messenger",
            "page_id": "988656934325292",  # Sao Việt page
            "object_id": "mid_sv_1",
            "thread_id": "psid_sv_1",
            "from_id": "psid_sv_1",
            "from_name": "Lê Thị Học",
            "body": "Tư vấn giúp em khoá học Excel văn phòng",
            "class": "faq",
            "created_ts": now - 1800,
        }, db_path=db_path)

        # Chạy backfill
        res = store.backfill_customers_from_events(db_path=db_path, days=30)
        assert res["events_scanned"] >= 2
        assert res["customers_created"] >= 2

        # Kiểm tra bảng customers
        bsn_custs = store.search_customers(brand="bsn", db_path=db_path)
        assert len(bsn_custs) == 1
        assert bsn_custs[0]["name"] == "Nguyễn Văn Game"
        assert bsn_custs[0]["brand"] == "bsn"
        assert "0987654321" in bsn_custs[0]["phones"]

        sv_custs = store.search_customers(brand="saoviet", db_path=db_path)
        assert len(sv_custs) == 1
        assert sv_custs[0]["name"] == "Lê Thị Học"
        assert sv_custs[0]["brand"] == "saoviet"


def test_rbac_backfill_permission():
    # Staff không được chạy backfill
    ok_staff, _ = ops_rbac.check_access_permission({"role": "staff"}, "/fanpage-care/customers/backfill", "POST")
    assert ok_staff is False

    # Manager và Owner được phép chạy backfill
    ok_mgr, _ = ops_rbac.check_access_permission({"role": "manager"}, "/fanpage-care/customers/backfill", "POST")
    assert ok_mgr is True

    ok_owner, _ = ops_rbac.check_access_permission({"role": "owner"}, "/fanpage-care/customers/backfill", "POST")
    assert ok_owner is True
