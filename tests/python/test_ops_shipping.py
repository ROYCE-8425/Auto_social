# -*- coding: utf-8 -*-
"""Unit and integration tests for Shipping Gateway, GHN Provider, Webhooks, and RBAC."""
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from _paths import ROOT, SERVER
import config
import ops_order_store
import ops_orders
import ops_shipping
import ops_shipping_store
from main import app


@pytest.fixture(autouse=True)
def setup_shipping_env(monkeypatch):
    """Thiết lập SQLite và cấu hình tạm thời cho Shipping Gateway."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        order_db = state_dir / "test_ops_orders.sqlite3"
        settings_file = state_dir / "test_ops_shipping_settings.json"

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(ops_order_store, "DEFAULT_DB_PATH", order_db)
        monkeypatch.setattr(ops_shipping_store, "DEFAULT_SETTINGS_PATH", settings_file)

        ops_order_store.init_db(order_db)

        yield {
            "state_dir": state_dir,
            "order_db": order_db,
            "settings_file": settings_file,
        }


def test_shipping_settings_can_be_configured_from_env(monkeypatch):
    monkeypatch.setenv("GHN_TOKEN", "test-ghn-token")
    monkeypatch.setenv("GHN_SHOP_ID", "123456")
    monkeypatch.setenv("GHN_CLIENT_ID", "client-abc")
    monkeypatch.setenv("GHN_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("GHN_PICKUP_DISTRICT_ID", "1442")
    monkeypatch.setenv("OPS_AUTO_CREATE_SHIPMENT", "true")

    settings = ops_shipping_store.load_shipping_settings()
    ghn = settings["providers"]["ghn"]

    assert ghn["enabled"] is True
    assert ghn["token"] == "test-ghn-token"
    assert ghn["shop_id"] == "123456"
    assert ghn["client_id"] == "client-abc"
    assert ghn["pickup_address"]["district_id"] == 1442
    assert settings["automation"]["auto_create_shipment"] is True


def test_ghn_not_configured_does_not_call_real_api():
    """1. Khi GHN chưa cấu hình Token / ShopId thì không gọi API thật mà báo lỗi not_configured."""
    order = ops_order_store.create_order(
        customer_name="Trần Văn Nam",
        customer_phone="0912345678",
        shipping_address="Số 10 Phố Chùa Láng, Đống Đa, Hà Nội",
        items=[{"name": "Chuột Silent", "price": 320000, "quantity": 1}],
        status="confirmed",
    )

    res = ops_orders.create_shipment_for_order(order["id"], provider_id="ghn", actor="staff_test")
    assert res["ok"] is False
    assert res["status"] == "not_configured"
    assert "chưa được cấu hình" in res["error"]


def test_ghn_configured_creates_shipment_via_provider_abstraction(monkeypatch):
    """2. Khi GHN đã cấu hình thì tạo vận đơn qua Provider Abstraction và cập nhật trạng thái."""
    # Mock GHNProvider.create_shipment để không gọi network ngoài khi test
    ghn = ops_shipping.get_shipping_provider("ghn")

    def mock_create_shipment(order_data, config):
        return {
            "ok": True,
            "provider": "ghn",
            "status": "ready_to_pick",
            "tracking_code": "GHN9988776655",
            "external_order_code": "GHN9988776655",
            "fee": 26000,
            "cod_amount": int(order_data.get("cod_amount") or 320000),
            "expected_delivery_time": "2026-10-02T18:00:00Z",
            "raw_response": {"order_code": "GHN9988776655", "total_fee": 26000},
        }

    monkeypatch.setattr(ghn, "is_configured", lambda cfg: True)
    monkeypatch.setattr(ghn, "create_shipment", mock_create_shipment)

    order = ops_order_store.create_order(
        customer_name="Hoàng Thị Mai",
        customer_phone="0987112233",
        shipping_address="Số 88 Cầu Giấy, Quan Hoa, Cầu Giấy, Hà Nội",
        items=[{"name": "Chuột Silent", "price": 320000, "quantity": 1}],
        status="confirmed",
    )

    res = ops_orders.create_shipment_for_order(order["id"], provider_id="ghn", actor="staff_test")
    assert res["ok"] is True
    assert "shipment" in res
    shipment = res["shipment"]
    assert shipment["tracking_code"] == "GHN9988776655"
    assert shipment["fee"] == 26000
    assert shipment["provider"] == "ghn"

    # Kiểm tra order cập nhật status thành shipment_created
    detail = ops_order_store.get_order(order["id"])
    assert detail["status"] == "shipment_created"
    assert detail["shipping_fee"] == 26000


def test_create_shipment_requires_confirmed_order(monkeypatch):
    """Không được tạo vận đơn thật từ đơn nháp hoặc đơn còn thiếu bước xác nhận."""
    ghn = ops_shipping.get_shipping_provider("ghn")
    monkeypatch.setattr(ghn, "is_configured", lambda cfg: True)
    monkeypatch.setattr(
        ghn,
        "create_shipment",
        lambda o, c: pytest.fail("Provider không được gọi khi đơn chưa confirmed"),
    )

    order = ops_order_store.create_order(
        customer_name="Nguyễn Văn A",
        customer_phone="0912345678",
        shipping_address="Số 10 Phố Chùa Láng, Đống Đa, Hà Nội",
        items=[{"name": "Sản phẩm test", "price": 100000, "quantity": 1}],
        status="ready_to_confirm",
    )

    with pytest.raises(ValueError, match="đã xác nhận"):
        ops_orders.create_shipment_for_order(order["id"], provider_id="ghn", actor="staff_test")


def test_ghn_webhook_updates_shipment_and_order_status(monkeypatch):
    """3. Webhook GHN nhận callback OrderCode và đồng bộ trạng thái bưu kiện & đơn hàng."""
    ghn = ops_shipping.get_shipping_provider("ghn")
    monkeypatch.setattr(ghn, "is_configured", lambda cfg: True)
    monkeypatch.setattr(
        ghn,
        "create_shipment",
        lambda o, c: {
            "ok": True,
            "provider": "ghn",
            "status": "ready_to_pick",
            "tracking_code": "GHN_WEBHOOK_TEST_01",
            "fee": 22000,
            "cod_amount": 200000,
        },
    )

    order = ops_order_store.create_order(
        customer_name="Phạm Bích",
        customer_phone="0933445566",
        shipping_address="Phường 2, Quận 3, TP.HCM",
        items=[{"name": "Sách Giáo trình", "price": 199000, "quantity": 1}],
        status="confirmed",
    )
    ops_orders.create_shipment_for_order(order["id"], provider_id="ghn")

    # Giả lập Webhook GHN bắn về trạng thái delivering -> shipping
    webhook_payload = {
        "OrderCode": "GHN_WEBHOOK_TEST_01",
        "Status": "delivering",
        "Description": "Bưu tá đang giao hàng tới người nhận",
        "Warehouse": "Kho Bưu cục Quận 3",
    }

    client = TestClient(app, base_url="http://127.0.0.1")
    wh_res = client.post("/ops/shipping/webhook/ghn", json=webhook_payload)
    assert wh_res.status_code == 200
    wh_data = wh_res.json()
    assert wh_data["ok"] is True
    assert wh_data["status"] == "shipping"

    # Kiểm tra đơn hàng cập nhật status
    order_detail = ops_order_store.get_order(order["id"])
    assert order_detail["status"] == "shipping"
    assert order_detail["shipment"]["status"] == "shipping"

    # Giả lập webhook báo đã giao thành công (delivered)
    client.post("/ops/shipping/webhook/ghn", json={"OrderCode": "GHN_WEBHOOK_TEST_01", "Status": "delivered"})
    order_delivered = ops_order_store.get_order(order["id"])
    assert order_delivered["status"] == "delivered"


def test_staff_cannot_modify_shipping_settings(monkeypatch):
    """4. Quyền RBAC: Staff không được sửa cài đặt vận chuyển (403), Manager/Owner được phép (200)."""
    import ops_rbac

    # 1. Staff cố gắng sửa cài đặt vận chuyển -> Bị chặn 403
    monkeypatch.setattr(
        ops_rbac,
        "get_current_ops_user",
        lambda req: {"username": "staff_nhanvien", "role": "staff", "name": "Nhân viên"},
    )
    client = TestClient(app, base_url="http://127.0.0.1")

    staff_res = client.post(
        "/ops/shipping/settings",
        json={"default_provider": "ghn", "automation": {"auto_create_shipment": True}},
    )
    assert staff_res.status_code == 403
    assert "Nhân viên không có quyền" in staff_res.json()["error"]

    # 2. Manager sửa cài đặt vận chuyển -> Thành công 200
    monkeypatch.setattr(
        ops_rbac,
        "get_current_ops_user",
        lambda req: {"username": "manager_quanly", "role": "manager", "name": "Quản lý"},
    )
    mgr_res = client.post(
        "/ops/shipping/settings",
        json={"default_provider": "ghn", "automation": {"auto_create_shipment": False}},
    )
    assert mgr_res.status_code == 200
    assert mgr_res.json()["ok"] is True


def test_audit_log_recorded_on_shipment_creation_and_cancellation(monkeypatch):
    """5. Audit log được ghi đầy đủ khi tạo và hủy vận đơn."""
    ghn = ops_shipping.get_shipping_provider("ghn")
    monkeypatch.setattr(ghn, "is_configured", lambda cfg: True)
    monkeypatch.setattr(
        ghn,
        "create_shipment",
        lambda o, c: {"ok": True, "provider": "ghn", "status": "ready_to_pick", "tracking_code": "GHN_LOG_01", "fee": 25000},
    )
    monkeypatch.setattr(ghn, "cancel_shipment", lambda t, c: {"ok": True, "status": "cancelled"})

    order = ops_order_store.create_order(
        customer_name="Vũ Đức",
        customer_phone="0911223344",
        shipping_address="123 Kim Mã, Ba Đình, Hà Nội",
        items=[{"name": "Combo Sách + Chuột", "price": 500000, "quantity": 1}],
        status="confirmed",
        actor="staff_test",
    )
    oid = order["id"]

    # Tạo shipment
    ops_orders.create_shipment_for_order(oid, provider_id="ghn", actor="staff_test")

    # Hủy shipment
    ops_orders.cancel_order_and_shipment(oid, reason="Khách yêu cầu dời lịch giao", actor="staff_test")

    # Kiểm tra audit logs
    order_detail = ops_order_store.get_order(oid)
    logs = order_detail["audit_logs"]
    actions = [log["action"] for log in logs]
    assert "shipment_created" in actions
    assert "cancelled" in actions


def test_mock_ghn_tracking_sync_updates_order_status():
    """Mock GHN cho phép test chức năng check trạng thái mà không cần token thật."""
    order = ops_order_store.create_order(
        customer_name="Nguyễn Minh Anh",
        customer_phone="0909000111",
        shipping_address="12 Nguyễn Trãi, Quận 1, TP.HCM",
        items=[{"name": "Bàn phím cơ Silent", "price": 850000, "quantity": 1}],
        status="confirmed",
        actor="staff_test",
    )
    shipment = ops_order_store.create_shipment(
        order_id=order["id"],
        provider="ghn",
        tracking_code="GHNMOCK-BD-002",
        external_order_code="GHNMOCK-BD-002",
        status="ready_to_pick",
        fee=26000,
        cod_amount=850000,
        provider_response={"mock": True},
        actor="staff_test",
    )

    res = ops_orders.sync_shipment_status(order["id"], actor="staff_test")
    assert res["ok"] is True
    assert res["shipment"]["id"] == shipment["id"]
    assert res["shipment"]["status"] == "delivered"
    assert res["order"]["status"] == "delivered"

    detail = ops_order_store.get_order(order["id"])
    actions = [log["action"] for log in detail["audit_logs"]]
    assert "status_update" in actions


def test_ops_sync_shipment_api_for_mock_ghn(monkeypatch):
    """API nút Check GHN cập nhật trạng thái từ mã mock trong bảng đơn hàng."""
    import ops_rbac

    monkeypatch.setattr(
        ops_rbac,
        "get_current_ops_user",
        lambda req: {"username": "staff_test", "role": "staff", "name": "Nhân viên Test"},
    )

    order = ops_order_store.create_order(
        customer_name="Lê Quốc Huy",
        customer_phone="0909000222",
        shipping_address="88 Đại lộ Bình Dương, Thủ Dầu Một",
        items=[{"name": "Combo tài liệu MOS", "price": 299000, "quantity": 1}],
        status="confirmed",
        actor="staff_test",
    )
    ops_order_store.create_shipment(
        order_id=order["id"],
        provider="ghn",
        tracking_code="GHNMOCK-HCM-001",
        external_order_code="GHNMOCK-HCM-001",
        status="ready_to_pick",
        fee=26000,
        cod_amount=299000,
        provider_response={"mock": True},
        actor="staff_test",
    )

    client = TestClient(app, base_url="http://127.0.0.1")
    res = client.post(f"/ops/orders/{order['id']}/sync-shipment")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["shipment"]["status"] == "shipping"
    assert data["order"]["status"] == "shipping"
