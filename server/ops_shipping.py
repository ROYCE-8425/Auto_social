"""Shipping Gateway Abstraction & Provider Implementations for Sèo Trum Ops.

Supports:
- BaseShippingProvider (interface chung)
- GHNProvider (Giao Hàng Nhanh v2 API)
- GHTKProvider & ViettelPostProvider (placeholders for roadmap)
- ShippingGateway dispatcher
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx

import ops_shipping_store

logger = logging.getLogger("ops_shipping")


class BaseShippingProvider(ABC):
    """Lớp cơ sở cho các đơn vị vận chuyển (Shipping Gateway Interface)."""

    provider_id: str
    name: str

    @abstractmethod
    def is_configured(self, config: Dict[str, Any]) -> bool:
        """Kiểm tra cấu hình provider đã đầy đủ credential hay chưa."""
        pass

    @abstractmethod
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Kiểm tra token và kết nối thực tế tới gateway API."""
        pass

    @abstractmethod
    def calculate_fee(self, order_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Tính cước phí vận chuyển và phụ phí COD."""
        pass

    @abstractmethod
    def create_shipment(self, order_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo vận đơn thật và trả về mã vận đơn (tracking_code), phí, thời gian dự kiến."""
        pass

    @abstractmethod
    def cancel_shipment(self, tracking_code: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Hủy vận đơn trên hệ thống hãng vận chuyển."""
        pass

    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Chuẩn hóa dữ liệu webhook/callback từ hãng về định dạng chung của Ops."""
        pass


class GHNProvider(BaseShippingProvider):
    """Triển khai tích hợp Giao Hàng Nhanh (GHN Express) v2 API."""

    provider_id = "ghn"
    name = "Giao Hàng Nhanh (GHN)"

    DEV_URL = "https://dev-online-gateway.ghn.vn/shiip/public-api"
    PROD_URL = "https://online-gateway.ghn.vn/shiip/public-api"

    def _get_base_url(self, config: Dict[str, Any]) -> str:
        env = str(config.get("environment") or "sandbox").strip().lower()
        return self.PROD_URL if env == "production" else self.DEV_URL

    def _get_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        token = str(config.get("token") or "").strip()
        shop_id = str(config.get("shop_id") or "").strip()
        headers = {
            "Content-Type": "application/json",
            "Token": token,
        }
        if shop_id:
            headers["ShopId"] = str(shop_id)
        return headers

    def is_configured(self, config: Dict[str, Any]) -> bool:
        token = str(config.get("token") or "").strip()
        shop_id = str(config.get("shop_id") or "").strip()
        return bool(token and shop_id)

    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured(config):
            return {
                "ok": False,
                "status": "not_configured",
                "error": "GHN Token và Shop ID chưa được cấu hình. Vui lòng nhập token tại Cài đặt Vận chuyển.",
            }

        url = f"{self._get_base_url(config)}/v2/shop/all"
        headers = self._get_headers(config)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json={"offset": 0, "limit": 10})
                data = resp.json()
                if resp.status_code == 200 and data.get("code") == 200:
                    shops = data.get("data", {}).get("shops", [])
                    return {
                        "ok": True,
                        "status": "connected",
                        "message": f"Kết nối GHN thành công! Tìm thấy {len(shops)} cửa hàng liên kết.",
                        "shops_count": len(shops),
                    }
                return {
                    "ok": False,
                    "status": "error",
                    "error": data.get("message") or f"Lỗi xác thực GHN (Mã: {data.get('code')})",
                }
        except Exception as exc:
            return {
                "ok": False,
                "status": "error",
                "error": f"Không thể kết nối đến máy chủ GHN: {exc}",
            }

    def calculate_fee(self, order_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured(config):
            # Fallback estimation nếu chưa cấu hình token thật
            return {
                "ok": True,
                "status": "estimated",
                "total_fee": 25000,
                "service_fee": 25000,
                "insurance_fee": 0,
                "note": "Ước tính nội thành tiêu chuẩn (Chưa cấu hình GHN Token thật)",
            }

        url = f"{self._get_base_url(config)}/v2/shipping-order/fee"
        headers = self._get_headers(config)
        pickup = config.get("pickup_address") or {}
        from_district = int(pickup.get("district_id") or 1442)

        # Trích xuất quận/huyện đích từ order
        addr = order_data.get("shipping_address_obj") or {}
        to_district = int(addr.get("district_id") or 1442)
        to_ward = str(addr.get("ward_code") or "1A0101")

        payload = {
            "service_type_id": 2,  # Chuẩn
            "from_district_id": from_district,
            "to_district_id": to_district,
            "to_ward_code": to_ward,
            "height": 10,
            "length": 20,
            "width": 15,
            "weight": max(200, int(order_data.get("weight_gram") or 500)),
            "insurance_value": min(5000000, int(order_data.get("total_amount") or 0)),
            "cod_failed_amount": 0,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                data = resp.json()
                if resp.status_code == 200 and data.get("code") == 200:
                    fee_data = data.get("data") or {}
                    return {
                        "ok": True,
                        "status": "calculated",
                        "total_fee": int(fee_data.get("total") or 25000),
                        "service_fee": int(fee_data.get("service_fee") or 25000),
                        "insurance_fee": int(fee_data.get("insurance_fee") or 0),
                    }
                return {
                    "ok": False,
                    "status": "error",
                    "error": data.get("message") or "Lỗi tính phí GHN",
                    "total_fee": 30000,  # safe default fallback
                }
        except Exception as exc:
            return {
                "ok": False,
                "status": "error",
                "error": f"Lỗi kết nối tính cước: {exc}",
                "total_fee": 30000,
            }

    def create_shipment(self, order_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured(config):
            return {
                "ok": False,
                "status": "not_configured",
                "error": "GHN Token và Shop ID chưa được cấu hình trong Cài Đặt Vận Chuyển.",
            }

        url = f"{self._get_base_url(config)}/v2/shipping-order/create"
        headers = self._get_headers(config)
        pickup = config.get("pickup_address") or {}

        # Parse shipping address
        addr = order_data.get("shipping_address_obj") or {}
        full_addr = str(order_data.get("shipping_address") or "").strip()
        to_name = str(order_data.get("customer_name") or "Khách hàng").strip()
        to_phone = str(order_data.get("customer_phone") or "").strip()

        items = order_data.get("items") or []
        ghn_items = []
        for it in items:
            ghn_items.append({
                "name": it.get("name") or "Sản phẩm",
                "code": it.get("sku") or "SKU",
                "quantity": int(it.get("quantity") or 1),
                "price": int(it.get("price") or 0),
            })
        if not ghn_items:
            ghn_items.append({
                "name": "Đơn hàng Sèo Trum Ops",
                "quantity": 1,
                "price": int(order_data.get("total_amount") or 0),
            })

        cod_amount = int(order_data.get("cod_amount") or 0)

        payload = {
            "payment_type_id": 2,  # Người nhận trả phí (hoặc 1 người gửi trả)
            "note": order_data.get("customer_notes") or "Cho xem hàng, không thử",
            "required_note": "CHOXEMHANGKHONGTHU",
            "from_name": pickup.get("name") or "Royce Shop",
            "from_phone": pickup.get("phone") or "0989819057",
            "from_address": pickup.get("address") or "72 Thành Thái, Phường 14, Quận 10",
            "from_ward_code": str(pickup.get("ward_code") or "20109"),
            "from_district_id": int(pickup.get("district_id") or 1442),
            "return_phone": pickup.get("phone") or "0989819057",
            "return_address": pickup.get("address") or "72 Thành Thái, Phường 14, Quận 10",
            "to_name": to_name,
            "to_phone": to_phone,
            "to_address": full_addr or "Địa chỉ giao hàng",
            "to_ward_code": str(addr.get("ward_code") or "1A0101"),
            "to_district_id": int(addr.get("district_id") or 1442),
            "cod_amount": cod_amount,
            "content": f"Đơn hàng #{order_data.get('id')}",
            "weight": 500,
            "length": 20,
            "width": 15,
            "height": 10,
            "service_type_id": 2,
            "items": ghn_items,
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                data = resp.json()
                if resp.status_code == 200 and data.get("code") == 200:
                    d = data.get("data") or {}
                    tracking_code = d.get("order_code")
                    fee = int(d.get("total_fee") or 0)
                    expected_time = d.get("expected_delivery_time")
                    return {
                        "ok": True,
                        "provider": "ghn",
                        "status": "ready_to_pick",
                        "tracking_code": tracking_code,
                        "external_order_code": tracking_code,
                        "fee": fee,
                        "cod_amount": cod_amount,
                        "expected_delivery_time": expected_time,
                        "raw_response": d,
                    }
                return {
                    "ok": False,
                    "status": "error",
                    "error": data.get("message") or f"Lỗi tạo vận đơn GHN ({data.get('code')})",
                    "raw_response": data,
                }
        except Exception as exc:
            return {
                "ok": False,
                "status": "error",
                "error": f"Lỗi kết nối cổng GHN: {exc}",
            }

    def cancel_shipment(self, tracking_code: str, config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured(config):
            return {
                "ok": True,
                "status": "cancelled",
                "message": "Đã hủy vận đơn nội bộ (Provider chưa cấu hình API)",
            }

        url = f"{self._get_base_url(config)}/v2/switch-status/cancel"
        headers = self._get_headers(config)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json={"order_codes": [tracking_code]})
                data = resp.json()
                if resp.status_code == 200 and data.get("code") == 200:
                    return {"ok": True, "status": "cancelled", "tracking_code": tracking_code}
                return {
                    "ok": False,
                    "error": data.get("message") or "Không thể hủy vận đơn trên GHN",
                }
        except Exception as exc:
            return {"ok": False, "error": f"Lỗi kết nối hủy đơn GHN: {exc}"}

    def _mock_tracking_status(self, tracking_code: str) -> Dict[str, Any]:
        code = str(tracking_code or "").strip().upper()
        scenarios = {
            "GHNMOCK-HCM-001": {
                "status": "shipping",
                "raw_status": "delivering",
                "description": "Mock GHN: Bưu tá đang giao hàng tới người nhận",
                "location": "Kho Quận 3 - TP.HCM",
            },
            "GHNMOCK-BD-002": {
                "status": "delivered",
                "raw_status": "delivered",
                "description": "Mock GHN: Đã giao hàng thành công",
                "location": "Bình Dương",
            },
        }
        status = scenarios.get(
            code,
            {
                "status": "shipping",
                "raw_status": "delivering",
                "description": "Mock GHN: Đơn hàng đang được luân chuyển",
                "location": "Kho trung chuyển GHN",
            },
        )
        return {
            "ok": True,
            "provider": "ghn",
            "tracking_code": tracking_code,
            "mock": True,
            "raw_response": {"mock": True, "order_code": tracking_code, **status},
            **status,
        }

    def check_tracking_status(self, tracking_code: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Chủ động tra cứu trạng thái vận đơn GHN theo order_code."""
        tracking = str(tracking_code or "").strip()
        if not tracking:
            return {"ok": False, "status": "missing_tracking", "error": "Thiếu mã vận đơn GHN để tra cứu."}

        if tracking.upper().startswith("GHNMOCK"):
            return self._mock_tracking_status(tracking)

        if not self.is_configured(config):
            return {
                "ok": False,
                "status": "not_configured",
                "error": "GHN Token và Shop ID chưa được cấu hình. Không thể tra cứu vận đơn thật.",
            }

        url = f"{self._get_base_url(config)}/v2/shipping-order/detail"
        headers = self._get_headers(config)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json={"order_code": tracking})
                data = resp.json()
                if resp.status_code == 200 and data.get("code") == 200:
                    d = data.get("data") or {}
                    leadtime_order = d.get("leadtime_order") or {}
                    payload = {
                        "OrderCode": d.get("order_code") or tracking,
                        "Status": d.get("status"),
                        "Description": d.get("status_name") or d.get("description"),
                        "Warehouse": d.get("current_warehouse_name") or leadtime_order.get("from_estimate_date"),
                    }
                    norm = self.parse_webhook(payload)
                    return {
                        "ok": True,
                        "provider": "ghn",
                        "tracking_code": tracking,
                        "status": norm["status"],
                        "raw_status": norm.get("raw_status"),
                        "description": norm.get("description"),
                        "location": norm.get("location"),
                        "raw_response": data,
                    }
                return {
                    "ok": False,
                    "status": "error",
                    "error": data.get("message") or f"Lỗi tra cứu vận đơn GHN ({data.get('code')})",
                    "raw_response": data,
                }
        except Exception as exc:
            return {"ok": False, "status": "error", "error": f"Lỗi kết nối tra cứu GHN: {exc}"}

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Chuẩn hóa GHN Webhook Payload:
        Trường GHN gửi: OrderCode, Status, Time, Description, Type, Fee, CodAmount.
        """
        raw_status = str(payload.get("Status") or payload.get("status") or "").strip().lower()
        tracking_code = str(payload.get("OrderCode") or payload.get("order_code") or "").strip()

        # Map GHN status to Ops status
        mapping = {
            "ready_to_pick": "picking",
            "picking": "picking",
            "storing": "picking",
            "delivering": "shipping",
            "delivered": "delivered",
            "delivery_fail": "delivery_fail",
            "cancel": "cancelled",
            "return": "returned",
            "returned": "returned",
            "damage": "failed",
            "lost": "failed",
        }
        normalized_status = mapping.get(raw_status, "shipping")
        description = payload.get("Description") or payload.get("description") or f"GHN cập nhật trạng thái: {raw_status}"

        return {
            "provider": "ghn",
            "tracking_code": tracking_code,
            "status": normalized_status,
            "raw_status": raw_status,
            "description": description,
            "location": payload.get("Warehouse") or payload.get("location") or "",
            "raw_payload": payload,
        }


# ============================================================
# Gateway Dispatcher & Factory
# ============================================================

_PROVIDERS: Dict[str, BaseShippingProvider] = {
    "ghn": GHNProvider(),
}


def get_shipping_provider(provider_id: str = "ghn") -> BaseShippingProvider:
    prov = _PROVIDERS.get(provider_id.lower())
    if not prov:
        raise ValueError(f"Đơn vị vận chuyển '{provider_id}' chưa được hỗ trợ.")
    return prov


def list_available_providers() -> list[dict]:
    settings = ops_shipping_store.load_shipping_settings()
    configured_providers = settings.get("providers", {})

    result = []
    # GHN
    ghn_cfg = configured_providers.get("ghn", {})
    ghn_obj = _PROVIDERS["ghn"]
    is_ghn_ready = ghn_obj.is_configured(ghn_cfg)
    result.append({
        "id": "ghn",
        "name": "Giao Hàng Nhanh (GHN Express)",
        "logo": "ghn",
        "supported": True,
        "is_default": settings.get("default_provider") == "ghn",
        "status": "ready" if is_ghn_ready else "not_configured",
        "status_label": "Đã sẵn sàng" if is_ghn_ready else "Chưa cấu hình",
        "capabilities": ["fee_calculation", "create_shipment", "cancel_shipment", "webhook"],
    })

    # GHTK
    result.append({
        "id": "ghtk",
        "name": "Giao Hàng Tiết Kiệm (GHTK)",
        "logo": "ghtk",
        "supported": False,
        "is_default": False,
        "status": "coming_soon",
        "status_label": "Đang chuẩn bị",
        "capabilities": ["fee_calculation", "create_shipment"],
    })

    # Viettel Post
    result.append({
        "id": "viettel_post",
        "name": "Viettel Post",
        "logo": "viettel_post",
        "supported": False,
        "is_default": False,
        "status": "coming_soon",
        "status_label": "Đang chuẩn bị",
        "capabilities": ["fee_calculation", "create_shipment"],
    })

    return result
