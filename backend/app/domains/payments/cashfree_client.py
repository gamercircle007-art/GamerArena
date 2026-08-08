"""Cashfree PG v4 thin client. Sandbox when keys set; mock order when not configured."""

from __future__ import annotations

import hashlib
import hmac
import base64
import logging
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

API_VERSION = "2023-08-01"


def is_configured(settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    return bool(
        (s.cashfree_app_id or "").strip() and (s.cashfree_secret_key or "").strip()
    )


def _base_url(settings: Settings) -> str:
    if (settings.cashfree_env or "sandbox").lower() == "production":
        return "https://api.cashfree.com/pg"
    return "https://sandbox.cashfree.com/pg"


def _headers(settings: Settings) -> dict[str, str]:
    return {
        "x-client-id": settings.cashfree_app_id,
        "x-client-secret": settings.cashfree_secret_key,
        "x-api-version": API_VERSION,
        "Content-Type": "application/json",
    }


def verify_webhook_signature(
    raw_body: bytes,
    timestamp: str,
    signature: str,
    secret: str,
) -> bool:
    """HMAC-SHA256 of timestamp + raw body, base64, constant-time compare."""
    if not secret or not signature or not timestamp:
        return False
    signed = f"{timestamp}".encode() + raw_body
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


async def create_order(
    *,
    order_id: str,
    amount_paise: int,
    customer_id: str,
    customer_phone: str,
    return_url: str,
    notify_url: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Create Cashfree order. amount_paise converted to rupees for API."""
    s = settings or get_settings()
    amount_rupees = (Decimal(amount_paise) / Decimal(100)).quantize(Decimal("0.01"))

    if not is_configured(s):
        # Dev / pre-keys: mock session so Flutter can complete pay-at-parlor path
        logger.info("cashfree_not_configured_mock_order order_id=%s", order_id)
        return {
            "status": "mock",
            "cf_order_id": f"mock_{order_id}",
            "payment_session_id": f"session_mock_{order_id}",
            "order_amount": float(amount_rupees),
            "order_currency": "INR",
        }

    payload = {
        "order_id": order_id,
        "order_amount": float(amount_rupees),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": customer_id[:50],
            "customer_phone": (customer_phone or "9999999999")[-10:],
        },
        "order_meta": {
            "return_url": return_url,
            "notify_url": notify_url,
        },
    }
    url = f"{_base_url(s)}/orders"
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(2):
            try:
                resp = await client.post(url, json=payload, headers=_headers(s))
                if resp.status_code >= 500 and attempt == 0:
                    continue
                resp.raise_for_status()
                data = resp.json()
                return {
                    "status": "created",
                    "cf_order_id": data.get("cf_order_id") or data.get("order_id"),
                    "payment_session_id": data.get("payment_session_id"),
                    "order_amount": data.get("order_amount"),
                    "order_currency": data.get("order_currency", "INR"),
                    "raw": data,
                }
            except httpx.HTTPError as exc:
                logger.warning("cashfree_create_order_failed attempt=%s err=%s", attempt, type(exc).__name__)
                if attempt == 1:
                    raise
    raise RuntimeError("cashfree create_order failed")


async def get_order(order_id: str, settings: Settings | None = None) -> dict[str, Any]:
    s = settings or get_settings()
    if not is_configured(s):
        return {"order_status": "ACTIVE", "order_id": order_id, "status": "mock"}
    url = f"{_base_url(s)}/orders/{order_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=_headers(s))
        resp.raise_for_status()
        return resp.json()
