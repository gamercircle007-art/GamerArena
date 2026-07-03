"""Parlour offer validation and discount calculation."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.gaming_booking.models import ParlourOffer
from app.domains.gaming_booking.repository import GamingBookingRepository


class OfferService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GamingBookingRepository(session)

    async def get_active_offers(self, parlour_id: UUID) -> list[ParlourOffer]:
        return await self.repo.list_active_offers(parlour_id)

    async def validate_offer(
        self,
        offer_id: UUID,
        parlour_id: UUID,
        *,
        hours_booked: Decimal,
    ) -> ParlourOffer:
        offer = await self.repo.get_offer_by_id(offer_id)
        if offer is None:
            raise NotFoundError("Offer not found")
        if offer.parlour_id != parlour_id:
            raise ValidationError("Offer does not apply to this parlor")
        if not offer.is_active:
            raise ValidationError("Offer is not active")

        now = datetime.now(UTC)
        if offer.valid_from and offer.valid_from.replace(tzinfo=UTC) > now:
            raise ValidationError("Offer is not yet valid")
        if offer.valid_until and offer.valid_until.replace(tzinfo=UTC) < now:
            raise ValidationError("Offer has expired")
        if offer.max_uses is not None and offer.current_uses >= offer.max_uses:
            raise ValidationError("Offer usage limit reached")
        if offer.min_hours is not None and hours_booked < offer.min_hours:
            raise ValidationError(f"Minimum {offer.min_hours} hours required for this offer")

        return offer

    def calculate_discount(
        self,
        offer: ParlourOffer | None,
        subtotal: Decimal,
    ) -> Decimal:
        if offer is None:
            return Decimal("0")

        discount = Decimal("0")
        if offer.discount_percent and offer.discount_percent > 0:
            discount = (subtotal * offer.discount_percent / Decimal("100")).quantize(
                Decimal("0.01")
            )
        if offer.discount_amount and offer.discount_amount > discount:
            discount = offer.discount_amount

        return min(discount, subtotal).quantize(Decimal("0.01"))

    async def increment_offer_usage(self, offer: ParlourOffer) -> None:
        offer.current_uses += 1
        await self.session.flush()