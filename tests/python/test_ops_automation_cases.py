# -*- coding: utf-8 -*-
"""Unit and integration tests for Automation Case Engine."""
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from _paths import ROOT, SERVER
import config
import ops_order_store
import ops_automation_engine
import ops_rbac
from main import app


@pytest.fixture(autouse=True)
def setup_automation_env(monkeypatch):
    """Thiết lập môi trường test SQLite cho Automation Case Engine."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        order_db = state_dir / "test_automation.sqlite3"

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(ops_order_store, "DEFAULT_DB_PATH", order_db)
        monkeypatch.setattr(ops_automation_engine, "KILL_SWITCH_FILE", state_dir / "ops_automation_kill_switch.json")

        ops_order_store.init_db(order_db)
        ops_automation_engine.set_kill_switch(False)

        current_user = {"username": "admin", "role": "admin", "name": "Admin Ops"}
        monkeypatch.setattr(ops_rbac, "get_current_ops_user", lambda request: current_user)

        # Tạo sẵn 1 sản phẩm kèm alias và page binding cho test
        prod = ops_order_store.create_product({
            "sku": "SKU-MOUSE-SL",
            "name": "Chuột Không Dây Silent Pro",
            "price": 250000,
            "sale_price": 220000,
            "stock": 35,
            "weight_gram": 200,
        })
        ops_order_store.add_product_alias(prod["id"], "chuột silent")
        ops_order_store.add_product_alias(prod["id"], "chuột không dây")
        ops_order_store.bind_product_to_page(prod["id"], page_id="page_tech_hub")

        yield {
            "state_dir": state_dir,
            "order_db": order_db,
            "product": prod,
            "set_role": lambda role: current_user.update({"role": role}),
        }


def test_kill_switch_blocks_all_automation():
    """Kiểm tra khi bật Kill Switch, mọi tác vụ tự động gửi tin hoặc tạo đơn đều bị chặn ngay."""
    ops_automation_engine.set_kill_switch(True)
    assert ops_automation_engine.get_kill_switch() is True

    res = ops_automation_engine.evaluate_and_run(
        thread_id="th_kill_01",
        page_id="page_tech_hub",
        messages=[{"sender": "customer", "text": "Chuột silent giá bao nhiêu shop?"}],
    )
    assert res["status"] == "skipped"
    assert res["reason"] == "kill_switch_active"

    # Outbox không được có tin nhắn nào
    outbox = ops_order_store.list_outbox_messages()
    assert len(outbox) == 0


def test_price_reply_case():
    """Kiểm tra case price_reply: AI nhận diện hỏi giá và trả lời đúng giá sản phẩm theo catalog."""
    res = ops_automation_engine.evaluate_and_run(
        thread_id="th_price_01",
        page_id="page_tech_hub",
        messages=[{"sender": "customer", "text": "chuột silent giá thế nào shop ơi?"}],
    )
    assert res["status"] == "success"
    assert res["case"] == "price_reply"
    assert any(p in res["reply_text"] for p in ("250,000", "250.000", "220,000", "220.000"))
    assert res["product_sku"] == "SKU-MOUSE-SL"

    # Tin nhắn đã được queue vào Outbox
    outbox = ops_order_store.list_outbox_messages(status="pending")
    assert len(outbox) == 1
    assert outbox[0]["thread_id"] == "th_price_01"


def test_stock_reply_case():
    """Kiểm tra case stock_reply: AI nhận diện hỏi còn hàng không và trả lời số lượng còn."""
    res = ops_automation_engine.evaluate_and_run(
        thread_id="th_stock_01",
        page_id="page_tech_hub",
        messages=[{"sender": "customer", "text": "chuột silent còn hàng không bạn?"}],
    )
    assert res["status"] == "success"
    assert res["case"] == "stock_reply"
    assert "35" in res["reply_text"] or "còn hàng" in res["reply_text"].lower()


def test_ask_missing_info_cases():
    """Kiểm tra case hỏi bổ sung SĐT hoặc Địa chỉ khi khách muốn chốt đơn nhưng thiếu thông tin."""
    # 1. Có địa chỉ nhưng thiếu SĐT
    res_phone = ops_automation_engine.evaluate_and_run(
        thread_id="th_missing_phone",
        page_id="page_tech_hub",
        messages=[{"sender": "customer", "text": "Gửi cho mình 1 chuột silent về số 15 ngõ 10 Đội Cấn Ba Đình Hà Nội nhé"}],
    )
    assert res_phone["status"] == "success"
    assert "ask_missing_phone" in res_phone["cases_executed"]
    assert "số điện thoại" in res_phone["reply_text"].lower()

    # 2. Có SĐT nhưng thiếu Địa chỉ
    res_addr = ops_automation_engine.evaluate_and_run(
        thread_id="th_missing_addr",
        page_id="page_tech_hub",
        messages=[{"sender": "customer", "text": "Ship cho mình 1 chuột silent, sđt 0987654321 nhé"}],
    )
    assert res_addr["status"] == "success"
    assert "ask_missing_address" in res_addr["cases_executed"]
    assert "địa chỉ" in res_addr["reply_text"].lower()


def test_unmatched_product_prohibits_auto_order():
    """Kiểm tra nguyên tắc cốt lõi: Sản phẩm không khớp catalog thì CẤM tạo đơn tự động."""
    res = ops_automation_engine.evaluate_and_run(
        thread_id="th_unmatched",
        page_id="page_tech_hub",
        messages=[{"sender": "customer", "text": "Ship cho anh 2 hộp sữa bắp tươi về số 1 Bà Triệu Hà Nội sđt 0912345678"}],
    )
    # Vì sữa bắp không có trong catalog của page_tech_hub nên không được tạo đơn
    assert "unmatched_product" in res["cases_evaluated"] or res["case"] in ("handoff_to_staff", "unmatched_product", "none")
    assert res.get("order_id") is None

    # Không có đơn nào trong DB
    orders = ops_order_store.list_orders()
    assert len(orders) == 0


def test_level_3_auto_order_and_shipment(monkeypatch):
    """Kiểm tra Cấp độ 3 (Full Auto): Tự động tạo đơn nháp -> duyệt đơn -> tạo vận đơn GHN -> gửi tracking code."""
    # Nâng cấu hình page_tech_hub lên Level 3 cho các case liên quan
    for c_type in ("create_order_draft", "auto_confirm_order", "auto_create_shipment", "send_tracking_code"):
        rule = ops_order_store.get_automation_rule(c_type, page_id="page_tech_hub")
        rule["level"] = 3
        rule["enabled"] = True
        rule["require_staff_approval"] = False
        ops_order_store.save_automation_rule(rule)

    # Mock GHN settings và API tạo vận đơn thành công
    import ops_shipping_store
    import ops_orders
    ops_shipping_store.save_shipping_settings({
        "default_provider": "ghn",
        "providers": {
            "ghn": {
                "token": "test_token_123",
                "shop_id": "test_shop_123",
            }
        }
    })

    def mock_create_shipment(order_id, provider_id="ghn", actor="auto_shipment_engine", db_path=None):
        ops_order_store.update_order(order_id, {"status": "confirmed", "tracking_code": "GHN-AUTO-TEST-8888"}, actor=actor, db_path=db_path)
        return {
            "ok": True,
            "shipment": {
                "id": "ship_test_123",
                "order_id": order_id,
                "tracking_code": "GHN-AUTO-TEST-8888",
                "provider": "ghn",
            },
        }

    monkeypatch.setattr(ops_orders, "create_shipment_for_order", mock_create_shipment)

    full_conversation = [
        {"sender": "customer", "text": "Lấy cho mình 1 chuột silent về số 25 Hai Bà Trưng, Tràng Tiền, Hoàn Kiếm, Hà Nội, sđt 0988112233 nhé shop"},
    ]

    res = ops_automation_engine.evaluate_and_run(
        thread_id="th_full_auto",
        page_id="page_tech_hub",
        messages=full_conversation,
    )

    assert res["status"] == "success"
    assert res["case"] in ("send_tracking_code", "auto_create_shipment", "auto_confirm_order", "create_order_draft")
    assert res.get("order_id") is not None
    assert res.get("tracking_code") == "GHN-AUTO-TEST-8888"

    # Kiểm tra đơn hàng trong DB đã được tạo và trạng thái confirmed
    saved_order = ops_order_store.get_order(res["order_id"])
    assert saved_order is not None
    assert saved_order["status"] in ("confirmed", "shipment_created")

    # Kiểm tra tin nhắn gửi tracking code đã nằm trong Outbox
    outbox = ops_order_store.list_outbox_messages()
    assert any("GHN-AUTO-TEST-8888" in (m.get("body") or m.get("message_text") or "") for m in outbox)


def test_api_automation_rules_and_rbac(setup_automation_env):
    """Kiểm tra API /ops/automation/rules và phân quyền RBAC."""
    client = TestClient(app, base_url="http://127.0.0.1")

    # 1. Admin lấy danh sách quy tắc
    res_get = client.get("/ops/automation/rules?page_id=page_tech_hub")
    assert res_get.status_code == 200
    assert len(res_get.json()["rules"]) >= 1

    # 2. Đổi sang Staff
    setup_automation_env["set_role"]("staff")

    # Staff không được sửa quy tắc
    res_mod = client.post("/ops/automation/rules", json={
        "case_type": "create_order_draft",
        "page_id": "page_tech_hub",
        "level": 3,
    })
    assert res_mod.status_code == 403

    # Staff không được bật/tắt Kill Switch
    res_ks = client.post("/ops/automation/kill-switch", json={"enabled": True})
    assert res_ks.status_code == 403
