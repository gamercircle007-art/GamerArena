"""OYO-style gaming parlor booking ORM models."""

import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableJSON, PortableTextArray


class GamingSlot(Base, UUIDPrimaryKeyMixin):
    """Bookable time slot at a gaming parlor."""

    __tablename__ = "gaming_slots"
    __table_args__ = ()

    parlour_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parlour_game_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    max_players: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_bookings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ParlourOffer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Discount offer for a gaming parlor."""

    __tablename__ = "parlour_offers"

    parlour_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    min_hours: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CancellationReason(Base, UUIDPrimaryKeyMixin):
    """Predefined cancellation reason for gaming bookings."""

    __tablename__ = "cancellation_reasons"

    label: Mapped[str] = mapped_column(String(100), nullable=False)
    requires_detail: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GamingBooking(Base, UUIDPrimaryKeyMixin):
    """User booking for a gaming parlor slot."""

    __tablename__ = "gaming_bookings"

    booking_ref: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parlour_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("gaming_slots.id", ondelete="SET NULL"),
        nullable=True,
    )
    offer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("parlour_offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    guest_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    num_players: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    slot_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    hours_booked: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    price_per_hour: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    final_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    payment_mode: Mapped[str] = mapped_column(String(30), default="pay_at_parlor", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    booking_status: Mapped[str] = mapped_column(String(20), default="confirmed", nullable=False, index=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cancellation_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    refund_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    free_cancellation_before: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_non_refundable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gc_points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Cashfree / virtual inventory (migration 021)
    station_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duration_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    units: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1)
    amount_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commission_paise: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    cf_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_session_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hold_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    @property
    def is_cancellation_free(self) -> bool:
        """True when cancellation is within the free window and booking is refundable."""
        if self.is_non_refundable or self.booking_status == "cancelled":
            return False
        if self.free_cancellation_before is None:
            return True
        deadline = self.free_cancellation_before
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        return datetime.now(UTC) < deadline


class ParlourRating(Base, UUIDPrimaryKeyMixin):
    """User review and ratings for a gaming parlor."""

    __tablename__ = "parlour_ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "gaming_place_id", name="uq_parlour_ratings_user_place"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    gaming_place_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    staff_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    location_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    cleanliness_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    checkin_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    is_verified_stay: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_photos: Mapped[list | None] = mapped_column(PortableTextArray, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class UserSearchHistory(Base, UUIDPrimaryKeyMixin):
    """Recent parlor search history for a user."""

    __tablename__ = "user_search_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    filters: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )