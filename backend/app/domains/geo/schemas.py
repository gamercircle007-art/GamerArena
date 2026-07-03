"""Geo domain Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NearbyParlorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    logo_url: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    game_types: list[str]
    is_verified: bool
    follower_count: int
    distance_meters: float
    lat: float | None = None
    lng: float | None = None
    rating: float | None = None
    phone: str | None = None
    website: str | None = None
    is_open: bool = True
    images: list[str] = Field(default_factory=list)


class ParlorSearchResponse(BaseModel):
    items: list[NearbyParlorResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class NearbyTournamentResponse(BaseModel):
    id: UUID
    parlor_id: UUID
    parlor_name: str
    title: str
    game_type: str
    start_time: datetime
    end_time: datetime
    total_slots: int
    booked_slots: int
    entry_fee: Decimal
    status: str
    distance_meters: float