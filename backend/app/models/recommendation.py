"""Recommendation / Algorithm models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, SmallInteger, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    view_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scroll_depth_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(30), nullable=True)
    position_in_feed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hour_of_day: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    day_of_week: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class UserInterestProfile(Base):
    __tablename__ = "user_interest_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    game_scores: Mapped[dict] = mapped_column(JSON, default=dict)  # JSONB in PG
    prefers_reels: Mapped[float] = mapped_column(Float, default=0.5)
    prefers_posts: Mapped[float] = mapped_column(Float, default=0.5)
    prefers_tournaments: Mapped[float] = mapped_column(Float, default=0.5)
    prefers_live: Mapped[float] = mapped_column(Float, default=0.5)
    creator_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    max_distance_km: Mapped[float] = mapped_column(Float, default=10.0)
    preferred_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    peak_hour_start: Mapped[int] = mapped_column(SmallInteger, default=18)
    peak_hour_end: Mapped[int] = mapped_column(SmallInteger, default=22)
    avg_session_duration_min: Mapped[float] = mapped_column(Float, default=5.0)
    exploration_rate: Mapped[float] = mapped_column(Float, default=0.1)
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    profile_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    last_computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ContentEngagementStats(Base):
    __tablename__ = "content_engagement_stats"

    content_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    content_type: Mapped[str] = mapped_column(String(30), primary_key=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    save_count: Mapped[int] = mapped_column(Integer, default=0)
    hide_count: Mapped[int] = mapped_column(Integer, default=0)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    booking_count: Mapped[int] = mapped_column(Integer, default=0)
    total_watch_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    avg_watch_pct: Mapped[float] = mapped_column(Float, default=0)
    replay_count: Mapped[int] = mapped_column(Integer, default=0)
    completion_rate: Mapped[float] = mapped_column(Float, default=0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0)
    trending_score: Mapped[float] = mapped_column(Float, default=0)
    virality_score: Mapped[float] = mapped_column(Float, default=0)
    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score_computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class TrendingItem(Base):
    __tablename__ = "trending_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    trending_score: Mapped[float] = mapped_column(Float, nullable=False)
    game_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    window: Mapped[str] = mapped_column(String(10), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FeedImpression(Base):
    __tablename__ = "feed_impressions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    feed_type: Mapped[str | None] = mapped_column(String(30), nullable=True)


class SearchEvent(Base):
    __tablename__ = "search_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    query_normalized: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    results_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clicked_content_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    clicked_content_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    click_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
