"""Recommendation schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TrackInteractionRequest(BaseModel):
    content_type: str
    content_id: UUID
    action: str
    view_duration_ms: int | None = None
    scroll_depth_pct: int | None = None
    session_id: UUID | None = None
    source: str | None = None
    position_in_feed: int | None = None
    user_lat: float | None = None
    user_lng: float | None = None
    device_type: str | None = None


class FeedItem(BaseModel):
    content_type: str
    content_id: UUID
    score: float
    is_trending: bool = False
    source_label: str


class FeedResponse(BaseModel):
    items: list[FeedItem]
    page: int
    feed_type: str
    personalized: bool


class UserInterestResponse(BaseModel):
    game_scores: dict[str, float]
    prefers_reels: float
    prefers_posts: float = 0.5
    prefers_tournaments: float = 0.5
    profile_confidence: float


class TrendingItemOut(BaseModel):
    content_id: UUID
    content_type: str
    trending_score: float
    window: str
    rank: int | None = None


class TrendingResponse(BaseModel):
    items: list[TrendingItemOut]
    window: str
    computed_at: datetime


class SearchResponse(BaseModel):
    query: str
    results: dict
    suggestions: list[str] = []


class AlgoStatsResponse(BaseModel):
    total_interactions: int
    profiles_computed: int
    trending_count: int
    avg_confidence: float | None = None
