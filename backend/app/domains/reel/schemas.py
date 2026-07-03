"""Reel domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.reel.models import ReelPrivacy


class ReelUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str | None = None
    name: str | None = Field(default=None, validation_alias="full_name")
    avatar_url: str | None = None
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False


class ReelCreate(BaseModel):
    video_url: str = Field(..., min_length=1, max_length=1024)
    thumbnail_url: str | None = Field(default=None, max_length=1024)
    cover_url: str | None = Field(default=None, max_length=1024)
    caption: str | None = Field(default=None, max_length=2200)
    hashtags: list[str] = Field(default_factory=list, max_length=30)
    location: str | None = Field(default=None, max_length=255)
    duration_seconds: int | None = Field(default=None, ge=1, le=30)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    aspect_ratio: str = Field(default="9:16", max_length=10)
    filter_name: str = Field(default="normal", max_length=50)
    music_title: str | None = Field(default=None, max_length=255)
    music_url: str | None = Field(default=None, max_length=1024)
    privacy: ReelPrivacy = ReelPrivacy.PUBLIC


class ReelUpdate(BaseModel):
    caption: str | None = Field(default=None, max_length=2200)
    privacy: ReelPrivacy | None = None
    cover_url: str | None = Field(default=None, max_length=1024)


class ReelResponse(BaseModel):
    id: UUID
    user: ReelUserSummary
    video_url: str
    thumbnail_url: str | None = None
    cover_url: str | None = None
    caption: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    location: str | None = None
    duration_seconds: int | None = None
    width: int | None = None
    height: int | None = None
    aspect_ratio: str = "9:16"
    filter_name: str = "normal"
    music_title: str | None = None
    music_url: str | None = None
    privacy: str
    likes_count: int
    comments_count: int
    views_count: int
    shares_count: int
    bookmarks_count: int
    is_liked: bool = False
    is_bookmarked: bool = False
    created_at: datetime


class ReelFeedResponse(BaseModel):
    items: list[ReelResponse]
    page: int
    limit: int
    has_more: bool


class ReelCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: UUID | None = None


class ReelCommentResponse(BaseModel):
    id: UUID
    user: ReelUserSummary
    content: str
    parent_id: UUID | None
    likes_count: int
    is_liked: bool = False
    is_pinned: bool = False
    is_deleted: bool = False
    reply_count: int = 0
    created_at: datetime


class ReelBookmarkResponse(BaseModel):
    bookmarked: bool
    bookmarks_count: int


class ReelViewResponse(BaseModel):
    views_count: int


class ReelShareResponse(BaseModel):
    shares_count: int
    share_url: str


class ReelReportCreate(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)


class UserFollowResponse(BaseModel):
    following: bool
    followers_count: int


class DemoMusicTrack(BaseModel):
    id: str
    title: str
    artist: str
    preview_url: str