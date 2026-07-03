"""Stories ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Story(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_url: Mapped[str] = mapped_column(String(500), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    privacy: Mapped[str] = mapped_column(String(20), default="friends", nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StoryView(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "story_views"

    story_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    viewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)