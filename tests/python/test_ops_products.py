# -*- coding: utf-8 -*-
"""Unit and integration tests for Product Catalog & Page Bindings."""
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from _paths import ROOT, SERVER
import config
import ops_order_store
import ops_rbac
from main import app


@pytest.fixture(autouse=True)
def setup_product_env(monkeypatch):
    """Thiết lập môi trường test SQLite cho Product Catalog."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        p = Path(td)
        state_dir = p / "state"
        state_dir.mkdir(parents=True)
        order_db = state_dir / "test_products.sqlite3"

        monkeypatch.setattr(config, "STATE_DIR", state_dir)
        monkeypatch.setattr(ops_order_store, "DEFAULT_DB_PATH", order_db)

        ops_order_store.init_db(order_db)

        # Mặc định mock role owner
        current_user = {"username": "boss", "role": "owner", "name": "Chủ shop"}
        monkeypatch.setattr(ops_rbac, "get_current_ops_user", lambda request: current_user)

        yield {
            "state_dir": state_dir,
            "order_db": order_db,
            "set_role": lambda role: current_user.update({"role": role}),
        }


def test_product_crud():
    """Kiểm tra tạo, đọc, cập nhật, xóa sản phẩm cơ bản."""
    # 1. Tạo sản phẩm
    prod = ops_order_store.create_product({
        "sku": "SKU-TEST-01",
        "name": "Chuột Gaming Không Dây X1",
        "description": "Chuột silent click độ phân giải cao",
        "price": 350000,
        "sale_price": 299000,
        "stock": 50,
        "weight_gram": 300,
        "category": "gaming",
    })
    assert prod["id"] is not None
    assert prod["sku"] == "SKU-TEST-01"
    assert prod["price"] == 350000
    assert prod["sale_price"] == 299000

    # 2. Đọc chi tiết sản phẩm
    fetched = ops_order_store.get_product(prod["id"])
    assert fetched is not None
    assert fetched["name"] == "Chuột Gaming Không Dây X1"

    # 3. Cập nhật sản phẩm
    updated = ops_order_store.update_product(prod["id"], {"stock": 45, "price": 340000})
    assert updated["stock"] == 45
    assert updated["price"] == 340000

    # 4. Tìm kiếm sản phẩm
    search_results = ops_order_store.search_products("gaming")
    assert len(search_results) >= 1
    assert search_results[0]["sku"] == "SKU-TEST-01"

    # 5. Xóa sản phẩm
    deleted = ops_order_store.delete_product(prod["id"])
    assert deleted is True
    assert ops_order_store.get_product(prod["id"]) is None


def test_product_aliases_and_variants():
    """Kiểm tra Alias từ khóa khách hay gọi và Biến thể của sản phẩm."""
    prod = ops_order_store.create_product({
        "sku": "SKU-KEY-RGB",
        "name": "Bàn Phím Cơ TKL Silent",
        "price": 850000,
        "stock": 20,
    })

    # Thêm các alias từ khóa
    a1 = ops_order_store.add_product_alias(prod["id"], "phím tkl silent")
    a2 = ops_order_store.add_product_alias(prod["id"], "bàn phím văn phòng êm")
    assert a1["alias"] == "phím tkl silent"

    # Thêm biến thể
    v1 = ops_order_store.create_product_variant(
        prod["id"],
        title="Màu Trắng Switch Red",
        sku="SKU-KEY-RGB-WHITE",
        price=890000,
        stock=10,
    )
    assert v1["sku"] == "SKU-KEY-RGB-WHITE"

    # Lấy lại chi tiết kiểm tra đã kèm aliases và variants
    detail = ops_order_store.get_product(prod["id"])
    assert len(detail["aliases"]) == 2
    assert "phím tkl silent" in detail["aliases"]
    assert len(detail["variants"]) == 1
    assert detail["variants"][0]["title"] == "Màu Trắng Switch Red"

    # Xóa alias
    assert ops_order_store.delete_product_alias(a1["id"]) is True
    detail_after = ops_order_store.get_product(prod["id"])
    assert len(detail_after["aliases"]) == 1


def test_page_scoped_bindings_and_custom_price():
    """Kiểm tra liên kết sản phẩm theo Page và ghi đè giá bán theo từng Page/Brand."""
    p1 = ops_order_store.create_product({
        "sku": "SKU-BOOK-EXCEL",
        "name": "Sách Tuyệt Kỹ Excel",
        "price": 200000,
        "stock": 100,
    })
    p2 = ops_order_store.create_product({
        "sku": "SKU-GAME-KEY",
        "name": "Bản Quyền Game BSN",
        "price": 500000,
        "stock": 50,
    })

    # Gắn p1 vào page_excel (với giá ưu đãi 180k)
    ops_order_store.bind_product_to_page(p1["id"], page_id="page_excel", custom_price=180000)
    # Gắn p2 vào page_gaming (với giá chuẩn)
    ops_order_store.bind_product_to_page(p2["id"], page_id="page_gaming")

    # Khi truy vấn catalog của page_excel: chỉ thấy p1, và giá là 180.000đ
    excel_prods = ops_order_store.list_products(page_id="page_excel")
    assert len(excel_prods) == 1
    assert excel_prods[0]["sku"] == "SKU-BOOK-EXCEL"
    assert excel_prods[0]["price"] == 180000

    # Khi truy vấn catalog của page_gaming: chỉ thấy p2
    gaming_prods = ops_order_store.list_products(page_id="page_gaming")
    assert len(gaming_prods) == 1
    assert gaming_prods[0]["sku"] == "SKU-GAME-KEY"
    assert gaming_prods[0]["price"] == 500000

    # Khi truy vấn page_unknown: không thấy sản phẩm nào
    assert len(ops_order_store.list_products(page_id="page_other")) == 0


def test_api_products_and_rbac(setup_product_env):
    """Kiểm tra REST API /ops/products và phân quyền RBAC (staff chỉ được xem, không được sửa)."""
    client = TestClient(app, base_url="http://127.0.0.1")

    # 1. Owner tạo sản phẩm qua API
    res = client.post("/ops/products", json={
        "sku": "SKU-API-01",
        "name": "Tai Nghe Chống Ồn ANC",
        "price": 600000,
        "stock": 30,
    })
    assert res.status_code == 200
    prod_id = res.json()["product"]["id"]

    # 2. Đổi quyền sang Staff
    setup_product_env["set_role"]("staff")

    # Staff được phép xem danh sách
    res_list = client.get("/ops/products")
    assert res_list.status_code == 200
    assert len(res_list.json()["products"]) >= 1

    # Staff KHÔNG được phép thêm sản phẩm mới
    res_add = client.post("/ops/products", json={
        "sku": "SKU-STAFF-FORBIDDEN",
        "name": "Sản phẩm lậu",
    })
    assert res_add.status_code == 403

    # Staff KHÔNG được phép xóa sản phẩm
    res_del = client.delete(f"/ops/products/{prod_id}")
    assert res_del.status_code == 403
