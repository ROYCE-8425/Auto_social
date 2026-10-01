# -*- coding: utf-8 -*-
"""Unit and integration tests for Social Commerce Order System (Order Core & AI Extraction)."""
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from _paths import ROOT, SERVER
import config
import ops_order_store
import ops_orders
import ops_sales_extraction
from main import app


@pytest.fixture(autouse=True)
def setup_order_env(monkeypatch):
    """Thiết lập SQLite và cấu hình tạm thời cho Order Core."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        order_db = state_dir / "test_ops_orders.sqlite3"

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(ops_order_store, "DEFAULT_DB_PATH", order_db)

        ops_order_store.init_db(order_db)
        ops_order_store.seed_demo_products(order_db)

        # Mock authentication cho ops user trong TestClient
        import ops_rbac
        monkeypatch.setattr(
            ops_rbac,
            "get_current_ops_user",
            lambda request: {"username": "staff_test", "role": "staff", "name": "Nhân viên Test"},
        )

        yield {
            "state_dir": state_dir,
            "order_db": order_db,
        }


def test_order_creation_from_inbox_complete_info():
    """1. Tạo order từ inbox với đầy đủ SĐT, địa chỉ và sản phẩm catalog hợp lệ."""
    messages = [
        {"sender": "user", "body": "Chào shop, mình muốn đặt mua 1 cuốn Sách Giáo trình Thủ thuật Excel nhé."},
        {"sender": "page", "body": "Dạ chào anh, anh cho em xin thông tin nhận hàng ạ."},
        {"sender": "user", "body": "Mình tên Hoàng Nam, SĐT: 0912345678, gửi về số 15 Lê Duẩn, Phường Bến Nghé, Quận 1, TP.HCM nhé. Ship COD nha shop."},
    ]

    extracted = ops_sales_extraction.extract_order_from_thread(messages)

    assert extracted["ok"] is True
    assert extracted["customer_phone"] == "0912345678"
    assert "15 Lê Duẩn" in extracted["shipping_address"]
    assert extracted["is_product_matched"] is True
    assert len(extracted["items"]) == 1
    assert extracted["items"][0]["sku"] == "SKU-BOOK-03"
    assert extracted["items"][0]["price"] == 199000
    assert extracted["total_amount"] == 199000
    assert extracted["missing_fields"] == []
    assert extracted["status"] == "ready_to_confirm"
    assert extracted["ai_confidence"] >= 0.85

    # Lưu thành đơn hàng
    order_res = ops_orders.create_new_order(extracted, actor="staff_test")
    assert order_res["ok"] is True
    order = order_res["order"]
    assert order["status"] == "ready_to_confirm"
    assert order["customer_phone"] == "0912345678"
    assert len(order["items"]) == 1


def test_order_extraction_missing_phone_results_in_needs_info():
    """2. Thiếu SĐT thì status là needs_info và missing_fields chứa 'phone'."""
    messages = [
        {"sender": "user", "body": "Ship cho mình 1 chuột không dây silent về số 25 phố Trần Phú, Hà Đông, Hà Nội nhé."},
    ]

    extracted = ops_sales_extraction.extract_order_from_thread(messages)

    assert extracted["ok"] is True
    assert extracted["customer_phone"] is None
    assert "Trần Phú" in extracted["shipping_address"]
    assert "phone" in extracted["missing_fields"]
    assert extracted["status"] == "needs_info"
    assert extracted["ai_confidence"] < 0.85
    # Tự sinh câu hỏi hỏi số điện thoại
    assert "số điện thoại" in extracted["followup_question"].lower()


def test_order_extraction_missing_address_results_in_needs_info():
    """3. Thiếu địa chỉ thì status là needs_info và missing_fields chứa 'address'."""
    messages = [
        {"sender": "user", "body": "Mình tên Tuấn Anh, SĐT 0988776655, cho mình đăng ký khoá học PowerBI nhé."},
    ]

    extracted = ops_sales_extraction.extract_order_from_thread(messages)

    assert extracted["ok"] is True
    assert extracted["customer_phone"] == "0988776655"
    assert extracted["shipping_address"] is None
    assert "address" in extracted["missing_fields"]
    assert extracted["status"] == "needs_info"
    # Tự sinh câu hỏi hỏi địa chỉ
    assert "địa chỉ" in extracted["followup_question"].lower()


def test_order_extraction_product_unmatched_requires_review():
    """4. Sản phẩm không match catalog thì đánh dấu và yêu cầu nhân viên xác nhận."""
    messages = [
        {"sender": "user", "body": "Shop có bán 2 hộp bánh trung thu thập cẩm không, ship cho mình về 10 Hàng Gai SĐT 0903112233."},
    ]

    extracted = ops_sales_extraction.extract_order_from_thread(messages)

    assert extracted["ok"] is True
    assert extracted["is_product_matched"] is False
    assert "product" in extracted["missing_fields"]
    assert extracted["status"] in ("needs_info", "draft")


def test_order_confirm_and_cancel_audit_logs():
    """5. Xác nhận đơn và hủy đơn ghi nhận đầy đủ audit log."""
    # 1. Tạo đơn nháp
    order = ops_order_store.create_order(
        customer_name="Lê Minh",
        customer_phone="0945112233",
        shipping_address="Tòa nhà Landmark 81, Bình Thạnh, TP.HCM",
        items=[{"name": "Bàn phím cơ Silent", "sku": "SKU-KEY-04", "quantity": 1, "price": 850000}],
        status="ready_to_confirm",
        actor="staff_test",
    )
    oid = order["id"]

    # 2. Xác nhận đơn
    conf_res = ops_orders.confirm_order(oid, actor="staff_test")
    assert conf_res["ok"] is True
    assert conf_res["order"]["status"] in ("confirmed", "shipment_created")

    # Kiểm tra audit log
    detail = ops_order_store.get_order(oid)
    actions = [log["action"] for log in detail["audit_logs"]]
    assert "created" in actions
    assert "confirmed" in actions

    # 3. Hủy đơn
    cancel_res = ops_orders.cancel_order_and_shipment(oid, reason="Khách đổi ý mua sau", actor="staff_test")
    assert cancel_res["ok"] is True
    assert cancel_res["order"]["status"] == "cancelled"

    detail2 = ops_order_store.get_order(oid)
    actions2 = [log["action"] for log in detail2["audit_logs"]]
    assert "cancelled" in actions2


def test_order_api_endpoints():
    """6. Kiểm thử các API /ops/orders qua FastAPI TestClient."""
    client = TestClient(app, base_url="http://127.0.0.1")

    # POST /ops/orders/extract-from-thread
    extract_res = client.post(
        "/ops/orders/extract-from-thread",
        json={
            "customer_name": "Đặng Thị Thảo",
            "messages": [
                {"sender": "user", "body": "Mình lấy 1 khóa học MOS nhé, SĐT 0978665544, địa chỉ số 9 Duy Tân, Cầu Giấy, Hà Nội"},
            ],
            "auto_save": True,
        },
    )
    assert extract_res.status_code == 200
    ext_data = extract_res.json()
    assert ext_data["ok"] is True
    assert "saved_order" in ext_data
    oid = ext_data["saved_order"]["id"]

    # GET /ops/orders/{id}
    get_res = client.get(f"/ops/orders/{oid}")
    assert get_res.status_code == 200
    assert get_res.json()["order"]["id"] == oid

    # POST /ops/orders/{id}/confirm
    confirm_res = client.post(f"/ops/orders/{oid}/confirm")
    assert confirm_res.status_code == 200
    assert confirm_res.json()["order"]["status"] in ("confirmed", "shipment_created")
