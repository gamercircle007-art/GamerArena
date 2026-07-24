"""Post ORM model."""

import uuid

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableJSON, PortableTextArray


class Post(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Social post published by a parlor (or user content for upload flow)."""

    __tablename__ = "posts"

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("tournaments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list[str]] = mapped_column(
        PortableTextArray,
        nullable=False,
        insert_default=list,
    )
    media_asset_ids: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # YouTube-style upload flow extensions
    post_type: Mapped[str] = mapped_column(String(20), nullable=False, default="post")
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    audience: Mapped[str] = mapped_column(String(20), nullable=False, default="everyone")
    game_types: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    tags: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    hashtags: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    mentions: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    location_parlor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="SET NULL"), nullable=True
    )
    allow_comments: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_remix: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_duet: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hide_likes: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_ai_content: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_paid_promo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_for_kids: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    thumbnail_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True
    )
    video_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True
    )
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="ready")