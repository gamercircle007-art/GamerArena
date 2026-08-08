"""Club promotion validation and discount application.

One entry point — `PromotionService.apply_best` — so a booking cannot be discounted
twice by two mechanisms. Discovery found the existing `ParlourOffer`/`OfferService`
promo path is wired into the legacy slot flow only (`create_booking_v2` hardcodes
`discount_amount = 0`); club promotions run through here for *both* paths, and the
resulting discount is recorded on `GamingBooking.club_discount_paise` so it is
distinguishable from a `ParlourOffer` discount in `discount_amount`.

Validation is deliberately explicit about *why* a promo failed — the owner-facing
promotions screen shows the reason rather than a bare "invalid".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as date_cls, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.club_ops.enums import PromotionType
from app.domains.club_ops.models import ClubCustomer, ClubPromotion
from app.domains.club_ops.pricing import BPS_ONE, _in_window
from app.domains.common.exceptions import NotFoundError, ValidationError

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class PromotionOutcome:
    """Result of evaluating one promotion against a booking context."""

    valid: bool
    discount_paise: int = 0
    promotion_id: UUID | None = None
    promotion_name: str | None = None
    promo_type: str | None = None
    reason: str | None = None

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "discount_paise": self.discount_paise,
            "promotion_id": str(self.promotion_id) if self.promotion_id else None,
            "promotion_name": self.promotion_name,
            "promo_type": self.promo_type,
            "reason": self.reason,
        }


class PromotionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_scoped(self, parlor_id: UUID, promotion_id: UUID) -> ClubPromotion:
        """Fetch a promotion, enforcing it belongs to this club."""
        promo = (
            await self.session.execute(
                select(ClubPromotion).where(
                    ClubPromotion.id == promotion_id,
                    ClubPromotion.parlor_id == parlor_id,
                )
            )
        ).scalar_one_or_none()
        if promo is None:
            raise NotFoundError("Promotion not found")
        return promo

    async def validate(
        self,
        *,
        parlor_id: UUID,
        subtotal_paise: int,
        resource_type: str,
        booking_date: date_cls,
        start_time: time,
        code: str | None = None,
        promotion_id: UUID | None = None,
        club_customer_id: UUID | None = None,
    ) -> PromotionOutcome:
        """Validate a specific promotion (by code or id) against a booking context."""
        promo: ClubPromotion | None = None
        if promotion_id is not None:
            promo = (
                await self.session.execute(
                    select(ClubPromotion).where(
                        ClubPromotion.id == promotion_id,
                        ClubPromotion.parlor_id == parlor_id,
                    )
                )
            ).scalar_one_or_none()
        elif code:
            promo = (
                await self.session.execute(
                    select(ClubPromotion).where(
                        ClubPromotion.parlor_id == parlor_id,
                        # Codes are entered by humans at a counter; match case-insensitively.
                        ClubPromotion.code.ilike(code.strip()),
                    )
                )
            ).scalar_one_or_none()

        if promo is None:
            return PromotionOutcome(valid=False, reason="Promotion not found for this club")

        customer = None
        if club_customer_id is not None:
            customer = (
                await self.session.execute(
                    select(ClubCustomer).where(
                        ClubCustomer.id == club_customer_id,
                        ClubCustomer.parlor_id == parlor_id,
                    )
                )
            ).scalar_one_or_none()

        return self._evaluate(
            promo,
            subtotal_paise=subtotal_paise,
            resource_type=resource_type,
            booking_date=booking_date,
            start_time=start_time,
            customer=customer,
        )

    async def apply_best(
        self,
        *,
        parlor_id: UUID,
        subtotal_paise: int,
        resource_type: str,
        booking_date: date_cls,
        start_time: time,
        code: str | None = None,
        club_customer_id: UUID | None = None,
    ) -> PromotionOutcome:
        """Pick the single best-value valid promotion.

        An explicit `code` is honoured exclusively: if the customer typed a code, they
        get that promo or an error explaining why not — silently substituting a
        different (even better) promo would be confusing at the counter.
        Otherwise all automatic promos (happy hour / first visit / loyalty) are
        evaluated and the largest discount wins.
        """
        if code:
            return await self.validate(
                parlor_id=parlor_id,
                subtotal_paise=subtotal_paise,
                resource_type=resource_type,
                booking_date=booking_date,
                start_time=start_time,
                code=code,
                club_customer_id=club_customer_id,
            )

        customer = None
        if club_customer_id is not None:
            customer = (
                await self.session.execute(
                    select(ClubCustomer).where(
                        ClubCustomer.id == club_customer_id,
                        ClubCustomer.parlor_id == parlor_id,
                    )
                )
            ).scalar_one_or_none()

        rows = (
            await self.session.execute(
                select(ClubPromotion).where(
                    ClubPromotion.parlor_id == parlor_id,
                    ClubPromotion.is_active.is_(True),
                    ClubPromotion.disabled_by_platform.is_(False),
                    # Code promos require the customer to present the code.
                    ClubPromotion.code.is_(None),
                )
            )
        ).scalars().all()

        best = PromotionOutcome(valid=False, reason="No applicable promotion")
        for promo in rows:
            outcome = self._evaluate(
                promo,
                subtotal_paise=subtotal_paise,
                resource_type=resource_type,
                booking_date=booking_date,
                start_time=start_time,
                customer=customer,
            )
            if outcome.valid and outcome.discount_paise > best.discount_paise:
                best = outcome
        return best

    async def list_for_club(
        self, parlor_id: UUID, *, active_only: bool = False
    ) -> list[ClubPromotion]:
        stmt = select(ClubPromotion).where(ClubPromotion.parlor_id == parlor_id)
        if active_only:
            stmt = stmt.where(
                ClubPromotion.is_active.is_(True),
                ClubPromotion.disabled_by_platform.is_(False),
            )
        rows = (await self.session.execute(stmt.order_by(ClubPromotion.created_at.desc()))).scalars()
        return list(rows)

    async def consume(self, promo: ClubPromotion) -> None:
        """Record one use. Called only once a booking is actually created."""
        promo.used_count += 1
        await self.session.flush()

    async def release(self, promo: ClubPromotion) -> None:
        """Give a use back when the booking it was applied to is cancelled."""
        promo.used_count = max(0, promo.used_count - 1)
        await self.session.flush()

    # ---- internals -------------------------------------------------------------

    def _evaluate(
        self,
        promo: ClubPromotion,
        *,
        subtotal_paise: int,
        resource_type: str,
        booking_date: date_cls,
        start_time: time,
        customer: ClubCustomer | None,
    ) -> PromotionOutcome:
        def fail(reason: str) -> PromotionOutcome:
            return PromotionOutcome(
                valid=False,
                promotion_id=promo.id,
                promotion_name=promo.name,
                promo_type=promo.promo_type,
                reason=reason,
            )

        if promo.disabled_by_platform:
            return fail(promo.disabled_reason or "Disabled by platform")
        if not promo.is_active:
            return fail("Promotion is not active")

        at = datetime.combine(booking_date, start_time, tzinfo=IST)
        if promo.valid_from is not None:
            valid_from = promo.valid_from
            if valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=UTC)
            if at < valid_from:
                return fail("Promotion has not started yet")
        if promo.valid_to is not None:
            valid_to = promo.valid_to
            if valid_to.tzinfo is None:
                valid_to = valid_to.replace(tzinfo=UTC)
            if at > valid_to:
                return fail("Promotion has expired")

        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            return fail("Promotion usage limit reached")

        applicable = promo.applicable_resource_types or []
        if applicable and resource_type not in applicable:
            return fail(f"Not applicable to {resource_type}")

        if promo.min_amount_paise is not None and subtotal_paise < promo.min_amount_paise:
            return fail(f"Minimum spend of ₹{promo.min_amount_paise / 100:.2f} required")

        if promo.promo_type == PromotionType.HAPPY_HOUR.value:
            if promo.happy_hour_start is None or promo.happy_hour_end is None:
                return fail("Happy hour window not configured")
            if not _in_window(start_time, promo.happy_hour_start, promo.happy_hour_end):
                return fail("Outside happy hour window")

        if promo.promo_type == PromotionType.FIRST_VISIT.value:
            # No customer record at all is still a first visit.
            if customer is not None and customer.visit_count > 0:
                return fail("Only valid on a first visit")

        if promo.promo_type == PromotionType.LOYALTY.value:
            required = promo.min_loyalty_points or 0
            available = customer.loyalty_points if customer else 0
            if available < required:
                return fail(f"Requires {required} loyalty points")

        discount = self._discount_for(promo, subtotal_paise)
        if discount <= 0:
            return fail("Promotion yields no discount")

        return PromotionOutcome(
            valid=True,
            discount_paise=discount,
            promotion_id=promo.id,
            promotion_name=promo.name,
            promo_type=promo.promo_type,
        )

    @staticmethod
    def _discount_for(promo: ClubPromotion, subtotal_paise: int) -> int:
        discount = 0
        if promo.percent_bps:
            discount = (subtotal_paise * promo.percent_bps) // BPS_ONE
            if promo.max_discount_paise is not None:
                discount = min(discount, promo.max_discount_paise)
        if promo.flat_paise and promo.flat_paise > discount:
            discount = promo.flat_paise
        # Never discount below zero-rupees payable.
        return max(0, min(discount, subtotal_paise))


def assert_promo_value(percent_bps: int | None, flat_paise: int | None) -> None:
    """Shared guard for create/update — mirrors the DB CHECK constraints so the API
    returns a 422 with a readable message instead of a raw IntegrityError."""
    if percent_bps is None and flat_paise is None:
        raise ValidationError("Provide either percent_bps or flat_paise")
    if percent_bps is not None and not (0 < percent_bps <= BPS_ONE):
        raise ValidationError("percent_bps must be between 1 and 10000 (10000 = 100%)")
    if flat_paise is not None and flat_paise <= 0:
        raise ValidationError("flat_paise must be greater than zero")
