"""Payment endpoints: Cashfree (primary) + Razorpay (legacy)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.booking.schemas import BookingResponse
from app.domains.booking.service import BookingService
from app.domains.payments import cashfree_client
from app.domains.payments.razorpay_stub import (
    create_order,
    get_public_key_id,
    is_configured,
    verify_payment_stub,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


class RazorpayConfigResponse(BaseModel):
    enabled: bool
    key_id: str | None = None


@router.get("/razorpay/config", response_model=RazorpayConfigResponse)
async def razorpay_config() -> RazorpayConfigResponse:
    """Public Razorpay key for client checkout (secret stays server-side)."""
    return RazorpayConfigResponse(enabled=is_configured(), key_id=get_public_key_id())


class CreateOrderRequest(BaseModel):
    amount_paise: int = Field(gt=0, description="Amount in paise (INR)")
    receipt: str = Field(min_length=1, max_length=40)


class CreateOrderResponse(BaseModel):
    order_id: str
    status: str
    amount_paise: int


class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


@router.post("/razorpay/order", response_model=CreateOrderResponse)
async def create_razorpay_order(body: CreateOrderRequest) -> CreateOrderResponse:
    result = create_order(body.amount_paise, body.receipt)
    if result.get("status") == "not_configured":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
        )
    return CreateOrderResponse(
        order_id=result["order_id"],
        status=result["status"],
        amount_paise=body.amount_paise,
    )


@router.post("/razorpay/verify")
async def verify_razorpay_payment(body: VerifyPaymentRequest) -> dict[str, str]:
    return verify_payment_stub(body.order_id, body.payment_id, body.signature)


class BookingPaymentOrderResponse(BaseModel):
    booking_id: str
    order_id: str
    amount_paise: int
    currency: str
    key_id: str | None = None


@router.post(
    "/razorpay/bookings/{booking_id}/order",
    response_model=BookingPaymentOrderResponse,
    summary="Create Razorpay order for a pending booking",
)
async def create_booking_payment_order(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> BookingPaymentOrderResponse:
    result = await BookingService(db).create_payment_order(booking_id, current_user.id)
    return BookingPaymentOrderResponse.model_validate(result)


@router.post(
    "/razorpay/bookings/{booking_id}/verify",
    response_model=BookingResponse,
    summary="Confirm Razorpay payment for a booking",
)
async def verify_booking_payment(
    booking_id: UUID,
    body: VerifyPaymentRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> BookingResponse:
    return await BookingService(db).confirm_payment(
        booking_id,
        current_user.id,
        body.order_id,
        body.payment_id,
        body.signature,
    )

# --- Cashfree (booking PG) ---


class CashfreeConfigResponse(BaseModel):
    enabled: bool
    env: str
    mock_mode: bool


@router.get("/cashfree/config", response_model=CashfreeConfigResponse)
async def cashfree_config() -> CashfreeConfigResponse:
    s = get_settings()
    enabled = cashfree_client.is_configured(s)
    return CashfreeConfigResponse(
        enabled=enabled,
        env=s.cashfree_env or "sandbox",
        mock_mode=not enabled,
    )


class CashfreeOrderRequest(BaseModel):
    booking_id: UUID
    return_url: str | None = None


class CashfreeOrderResponse(BaseModel):
    booking_id: str
    cf_order_id: str
    payment_session_id: str | None = None
    order_amount: float
    order_currency: str = "INR"
    status: str
    mock_mode: bool = False


@router.post(
    "/cashfree/bookings/{booking_id}/order",
    response_model=CashfreeOrderResponse,
    summary="Create Cashfree order for a gaming booking",
)
async def create_cashfree_booking_order(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    body: CashfreeOrderRequest | None = None,
) -> CashfreeOrderResponse:
    from decimal import Decimal

    from app.domains.gaming_booking.service import GamingBookingService

    svc = GamingBookingService(db)
    booking = await svc.get_booking(booking_id, user_id=current_user.id)
    if booking.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Already paid")
    amount = booking.final_price or booking.total_price or Decimal("0")
    amount_paise = int(amount * 100)
    if amount_paise <= 0:
        raise HTTPException(status_code=400, detail="Invalid booking amount")

    s = get_settings()
    return_url = (body.return_url if body else None) or s.cashfree_return_url
    notify_url = s.cashfree_notify_url or ""
    phone = booking.contact_phone or current_user.phone or "9999999999"

    order = await cashfree_client.create_order(
        order_id=str(booking.booking_ref or booking_id),
        amount_paise=amount_paise,
        customer_id=str(current_user.id),
        customer_phone=phone,
        return_url=return_url,
        notify_url=notify_url,
        settings=s,
    )
    return CashfreeOrderResponse(
        booking_id=str(booking_id),
        cf_order_id=str(order.get("cf_order_id") or ""),
        payment_session_id=order.get("payment_session_id"),
        order_amount=float(order.get("order_amount") or amount),
        order_currency=str(order.get("order_currency") or "INR"),
        status=str(order.get("status") or "created"),
        mock_mode=order.get("status") == "mock",
    )


@router.post("/webhooks/cashfree", include_in_schema=False)
async def cashfree_webhook(request: Request) -> dict[str, str]:
    """Cashfree webhook — verify signature, acknowledge; process async later."""
    s = get_settings()
    raw = await request.body()
    ts = request.headers.get("x-webhook-timestamp") or ""
    sig = request.headers.get("x-webhook-signature") or ""
    secret = (s.cashfree_webhook_secret or "").strip()

    if secret:
        ok = cashfree_client.verify_webhook_signature(raw, ts, sig, secret)
        if not ok:
            raise HTTPException(status_code=401, detail="invalid webhook signature")

    # Parse lightly for logging only (no secrets)
    try:
        import json

        payload = json.loads(raw.decode() or "{}")
        event_type = payload.get("type") or payload.get("event") or "unknown"
    except Exception:  # noqa: BLE001
        event_type = "parse_error"

    # Full ledger/booking update via Celery in a follow-up; acknowledge now.
    return {"status": "ok", "event": str(event_type)}
