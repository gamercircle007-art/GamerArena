"""Snap map and extended profile ORM models."""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableTextArray


class UserLocation(Base, TimestampMixin):
    __tablename__ = "user_locations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    ghost_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    location_privacy: Mapped[str] = mapped_column(String(20), default="friends", nullable=False)


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    game_tags: Mapped[list[str] | None] = mapped_column(PortableTextArray, nullable=True)
    website: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_messages_from: Mapped[str] = mapped_column(String(20), default="friends", nullable=False)
    show_online_status: Mapped[str] = mapped_column(String(20), default="friends", nullable=False)
    allow_friend_requests: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    profile_qr_code: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)


class CloseFriend(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "close_friends"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    friend_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )