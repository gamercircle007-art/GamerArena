"""Gaming place ORM models — bound to the projectX ``gaming_places`` catalog."""

import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import Boolean, Float, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import PortableJSON


class GamingPlace(Base):
    """Venue row synced from the external ``gaming_places`` table."""

    __tablename__ = "gaming_places"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    google_place_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_ratings_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    business_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    primary_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    types: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    opening_hours: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    photo_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    photos: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)


class GamingPlaceExtension(Base, TimestampMixin):
    """App-specific overlay for a synced gaming place (follows, posts, ownership)."""

    __tablename__ = "gaming_place_extensions"

    gaming_place_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        primary_key=True,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    follower_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    price_per_hour: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    base_tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("18"), nullable=False)
    equipment_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    staff_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    checkin_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    is_wizard_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_couples_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)