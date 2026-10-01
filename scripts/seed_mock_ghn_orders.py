"""Seed 2 mock GHN orders for testing the Ops order tracking UI.

Run:
    python scripts/seed_mock_ghn_orders.py
"""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))

import ops_order_store  # noqa: E402
import ops_orders  # noqa: E402


MOCK_ORDERS = [
    {
        "thread_id": "mock-ghn-hcm-001",
        "customer_name": "Nguyen Minh Anh",
        "customer_phone": "0909000111",
        "shipping_address": "12 Nguyen Trai, Quan 1, TP.HCM",
        "items": [{"sku": "SKU-KEY-04", "name": "Ban phim co Silent", "price": 850000, "quantity": 1}],
        "tracking_code": "GHNMOCK-HCM-001",
        "fee": 26000,
        "expected_status": "shipping",
    },
    {
        "thread_id": "mock-ghn-bd-002",
        "customer_name": "Le Quoc Huy",
        "customer_phone": "0909000222",
        "shipping_address": "88 Dai lo Binh Duong, Thu Dau Mot",
        "items": [{"sku": "SKU-MOS-01", "name": "Combo tai lieu MOS", "price": 299000, "quantity": 1}],
        "tracking_code": "GHNMOCK-BD-002",
        "fee": 26000,
        "expected_status": "delivered",
    },
]


def _find_order_by_thread(thread_id: str) -> dict | None:
    matches = ops_order_store.list_orders(thread_id=thread_id, limit=1)
    if not matches:
        return None
    return ops_order_store.get_order(matches[0]["id"])


def _ensure_mock_order(spec: dict) -> dict:
    order = _find_order_by_thread(spec["thread_id"])
    created = False
    if not order:
        order = ops_order_store.create_order(
            customer_name=spec["customer_name"],
            customer_phone=spec["customer_phone"],
            thread_id=spec["thread_id"],
            page_id="mock_ops_page",
            shipping_address=spec["shipping_address"],
            items=spec["items"],
            status="confirmed",
            source="mock_ghn_seed",
            actor="seed_mock_ghn",
        )
        created = True

    shipment = order.get("shipment")
    if not shipment:
        ops_order_store.create_shipment(
            order_id=order["id"],
            provider="ghn",
            tracking_code=spec["tracking_code"],
            external_order_code=spec["tracking_code"],
            status="ready_to_pick",
            fee=spec["fee"],
            cod_amount=int(order.get("cod_amount") or order.get("total_amount") or 0),
            provider_response={"mock": True, "seed": "seed_mock_ghn_orders"},
            actor="seed_mock_ghn",
        )

    sync = ops_orders.sync_shipment_status(order["id"], actor="seed_mock_ghn")
    refreshed = ops_order_store.get_order(order["id"]) or order
    return {
        "created": created,
        "id": refreshed["id"],
        "customer_name": refreshed.get("customer_name"),
        "order_status": refreshed.get("status"),
        "tracking_code": refreshed.get("shipment", {}).get("tracking_code") if refreshed.get("shipment") else None,
        "shipment_status": refreshed.get("shipment", {}).get("status") if refreshed.get("shipment") else None,
        "sync_ok": bool(sync.get("ok")),
    }


def main() -> int:
    ops_order_store.init_db()
    seeded = [_ensure_mock_order(spec) for spec in MOCK_ORDERS]
    print("Seeded mock GHN orders:")
    for item in seeded:
        state = "created" if item["created"] else "exists"
        print(
            f"- {item['id']} [{state}] {item['customer_name']} | "
            f"{item['tracking_code']} | order={item['order_status']} shipment={item['shipment_status']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
