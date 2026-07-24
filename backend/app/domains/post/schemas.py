"""Post domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.parlor.schemas import ParlorSummary


class TournamentPostSummary(BaseModel):
    id: UUID
    title: str


class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    media_urls: list[str] = Field(default_factory=list, max_length=10)
    tournament_id: UUID | None = None
    parlor_id: UUID | None = None
    # YouTube upload extensions
    post_type: str = "post"
    title: str | None = None
    description: str | None = None
    visibility: str = "public"
    audience: str = "everyone"
    game_types: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    location_parlor_id: UUID | None = None
    allow_comments: bool = True
    allow_remix: bool = True
    allow_duet: bool = True
    hide_likes: bool = False
    is_ai_content: bool = False
    is_paid_promo: bool = False
    is_for_kids: bool = False
    duration_seconds: float | None = None
    thumbnail_asset_id: UUID | None = None
    video_asset_id: UUID | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    media_urls: list[str]
    parlor: ParlorSummary
    tournament: TournamentPostSummary | None = None
    likes_count: int
    comments_count: int
    is_liked: bool = False
    created_at: datetime
    # extensions
    post_type: str = "post"
    title: str | None = None
    description: str | None = None
    visibility: str = "public"
    game_types: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)