"""Stations, hours, holds, ledger, webhooks — Cashfree onboarding schema."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableJSON


class ParlorStation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "parlor_stations"
    __table_args__ = (UniqueConstraint("parlor_id", "station_type", name="uq_parlor_stations_type"),)

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    station_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PC, PS5, XBOX, VR, POOL
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hourly_price_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=9900)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    specs: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)


class ParlorHours(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "parlor_hours"
    __table_args__ = (
        UniqueConstraint("parlor_id", "weekday", "open_time", name="uq_parlor_hours_shift"),
    )

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0=Mon .. 6=Sun
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)


class ParlorClosure(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "parlor_closures"
    __table_args__ = (UniqueConstraint("parlor_id", "date", name="uq_parlor_closures_date"),)

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class BookingHold(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "booking_holds"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_bookings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    station_type: Mapped[str] = mapped_column(String(20), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_hours: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    units: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    released: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class PaymentLedger(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "payment_ledger"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False)  # payment, refund, commission
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    cf_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cf_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    balance_direction: Mapped[str] = mapped_column(String(10), nullable=False)  # credit, debit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class WebhookEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "webhook_events"

    provider: Mapped[str] = mapped_column(String(30), default="cashfree", nullable=False)
    event_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class BookingAudit(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "booking_audit"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    actor: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class ReconciliationIssue(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "reconciliation_issues"

    booking_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    cf_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
