"""Razorpay payment integration — real SDK when configured, local dev fallback."""

from app.core.config import Settings, get_settings


def is_configured(settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    return bool(cfg.razorpay_key_id and cfg.razorpay_key_secret)


def get_public_key_id() -> str | None:
    cfg = get_settings()
    return cfg.razorpay_key_id or None


def _client(settings: Settings):
    import razorpay

    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def create_order(amount_paise: int, receipt: str) -> dict[str, str | int]:
    settings = get_settings()
    if not is_configured(settings):
        if settings.app_env == "local":
            return {
                "status": "created",
                "order_id": f"order_dev_{receipt}",
                "amount_paise": amount_paise,
                "key_id": None,
            }
        return {"status": "not_configured", "order_id": "stub", "key_id": None}

    client = _client(settings)
    order = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt[:40],
            "payment_capture": 1,
        }
    )
    return {
        "status": "created",
        "order_id": order["id"],
        "amount_paise": amount_paise,
        "key_id": settings.razorpay_key_id,
    }


def verify_payment_stub(order_id: str, payment_id: str, signature: str) -> dict[str, str]:
    settings = get_settings()
    if not is_configured(settings):
        if settings.app_env == "local":
            return {"status": "verified_dev", "order_id": order_id, "payment_id": payment_id}
        return {"status": "not_configured", "order_id": order_id, "payment_id": payment_id}

    client = _client(settings)
    client.utility.verify_payment_signature(
        {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        }
    )
    return {"status": "verified", "order_id": order_id, "payment_id": payment_id}