"""Tournament and booking ORM models."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableJSON


class Tournament(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tournament hosted by a parlor."""

    __tablename__ = "tournaments"

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    game_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    booked_slots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    entry_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    prizes: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)


class Booking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User booking for a tournament slot."""

    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("tournament_id", "slot_number", name="uq_bookings_tournament_slot"),
        UniqueConstraint("tournament_id", "user_id", name="uq_bookings_tournament_user"),
    )

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="confirmed", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)