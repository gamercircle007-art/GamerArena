"""Reel ORM models."""

import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableTextArray


class ReelPrivacy(str, enum.Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"
    UNLISTED = "unlisted"
    INTERNATIONAL = "international"
    COUNTRY_ONLY = "country_only"
    FOLLOWERS = "followers"
    NEARBY = "nearby"
    AGE_RESTRICTED = "age_restricted"


class Reel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reels"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list[str]] = mapped_column(PortableTextArray, default=list)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="9:16", nullable=False)
    filter_name: Mapped[str] = mapped_column(String(50), default="normal", nullable=False)
    music_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    music_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    privacy: Mapped[str] = mapped_column(String(30), default=ReelPrivacy.PUBLIC.value, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bookmarks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ReelComment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reel_comments"

    reel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("reel_comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ReelBookmark(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reel_bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "reel_id", name="uq_reel_bookmarks_user_reel"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reels.id", ondelete="CASCADE"), nullable=False, index=True
    )


class ReelView(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reel_views"

    reel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )


class UserFollow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_user_follows_pair"),)

    follower_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )


class ReelReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reel_reports"

    reel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)