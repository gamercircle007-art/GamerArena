"""Parlor domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParlorSummary(BaseModel):
    """Minimal parlor info nested in tournament/post responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    logo_url: str | None = None
    is_verified: bool = False


class ParlorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    logo_url: str | None = None
    address: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    game_types: list[str] = Field(default_factory=list, max_length=20)


class ParlorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    logo_url: str | None = None
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    game_types: list[str] | None = None


class ParlorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID | None = None
    name: str
    description: str | None = None
    logo_url: str | None = None
    address: str | None = None
    game_types: list[str]
    is_verified: bool
    follower_count: int
    post_count: int
    is_following: bool = False
    rating: float | None = None
    phone: str | None = None
    website: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
    updated_at: datetime


class TournamentBookingStat(BaseModel):
    tournament_id: UUID
    title: str
    bookings_count: int


class ParlorAnalyticsResponse(BaseModel):
    follower_count: int
    total_posts: int
    upcoming_tournaments_count: int
    total_bookings_this_month: int
    bookings_by_tournament: list[TournamentBookingStat]