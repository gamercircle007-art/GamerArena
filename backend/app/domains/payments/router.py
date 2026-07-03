"""Razorpay payment endpoints (Phase 3 scaffold)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.booking.schemas import BookingResponse
from app.domains.booking.service import BookingService
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