"""Shipping Settings and Provider Configuration Store for Sèo Trum Ops.

Manages persistent carrier configurations (GHN, GHTK, Viettel Post) and automation rules.
File location: STATE_DIR / "ops_shipping_settings.json".
Tokens are stored securely in settings file and masked on read for UI/client.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import config

DEFAULT_SETTINGS_PATH = config.STATE_DIR / "ops_shipping_settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "default_provider": "ghn",
    "providers": {
        "ghn": {
            "name": "Giao Hàng Nhanh (GHN Express)",
            "enabled": False,
            "token": "",
            "shop_id": "",
            "client_id": "",
            "environment": "sandbox",  # sandbox | production
            "pickup_address": {
                "name": "Kho Sèo Trum Ops",
                "phone": "0987654321",
                "address": "Số 10 Phố Chùa Láng",
                "ward_code": "1A0101",
                "district_id": 1442,
                "province_name": "Hà Nội",
            },
        },
        "ghtk": {
            "name": "Giao Hàng Tiết Kiệm (GHTK)",
            "enabled": False,
            "status": "coming_soon",
            "token": "",
        },
        "viettel_post": {
            "name": "Viettel Post",
            "enabled": False,
            "status": "coming_soon",
            "token": "",
        },
    },
    "automation": {
        "auto_create_shipment": False,  # Mặc định KHÔNG tự tạo vận đơn nếu chưa bật rule
        "min_confidence": 0.85,
        "require_sku_match": True,
        "max_cod_amount": 5000000,
        "kill_switch": False,
    },
}


def load_shipping_settings(settings_path: Path | str | None = None) -> Dict[str, Any]:
    p = Path(settings_path or DEFAULT_SETTINGS_PATH)
    if not p.is_file():
        return json.loads(json.dumps(DEFAULT_SETTINGS))
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        merged = json.loads(json.dumps(DEFAULT_SETTINGS))
        if "default_provider" in data:
            merged["default_provider"] = data["default_provider"]
        if "providers" in data and isinstance(data["providers"], dict):
            for k, v in data["providers"].items():
                if k in merged["providers"]:
                    merged["providers"][k].update(v)
                else:
                    merged["providers"][k] = v
        if "automation" in data and isinstance(data["automation"], dict):
            merged["automation"].update(data["automation"])
        return merged
    except Exception:
        return json.loads(json.dumps(DEFAULT_SETTINGS))


def save_shipping_settings(settings: Dict[str, Any], settings_path: Path | str | None = None) -> Dict[str, Any]:
    p = Path(settings_path or DEFAULT_SETTINGS_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    current = load_shipping_settings(settings_path)

    if "default_provider" in settings:
        current["default_provider"] = str(settings["default_provider"]).strip().lower()

    if "providers" in settings and isinstance(settings["providers"], dict):
        for prov_id, prov_cfg in settings["providers"].items():
            if prov_id in current["providers"] and isinstance(prov_cfg, dict):
                # Giữ nguyên token cũ nếu client truyền masked token "***"
                if "token" in prov_cfg:
                    new_token = str(prov_cfg["token"]).strip()
                    if "***" in new_token or not new_token:
                        # Do not overwrite with mask if token already existed and not changing
                        if "***" in new_token:
                            prov_cfg["token"] = current["providers"][prov_id].get("token", "")
                current["providers"][prov_id].update(prov_cfg)

    if "automation" in settings and isinstance(settings["automation"], dict):
        current["automation"].update(settings["automation"])

    p.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    return current


def mask_token(token: str) -> str:
    if not token or len(token) < 8:
        return ""
    return token[:4] + "***" + token[-4:]


def get_public_shipping_settings(settings_path: Path | str | None = None, include_token: bool = False) -> Dict[str, Any]:
    """Trả về shipping settings an toàn cho client: mask token trừ khi include_token=True (dành cho Owner/Manager)."""
    raw = load_shipping_settings(settings_path)
    safe = json.loads(json.dumps(raw))
    for prov_id, prov in safe.get("providers", {}).items():
        if "token" in prov:
            t = prov.get("token") or ""
            prov["has_token"] = bool(t)
            prov["masked_token"] = mask_token(t)
            if not include_token:
                prov["token"] = mask_token(t)
    return safe
