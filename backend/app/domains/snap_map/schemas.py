"""Snap map and profile API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LocationUpdate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy: float | None = None


class GhostModeUpdate(BaseModel):
    enabled: bool


class LocationPrivacyUpdate(BaseModel):
    privacy: str = Field(pattern="^(everyone|friends|nobody)$")


class SnapMapUser(BaseModel):
    user_id: UUID
    name: str | None = None
    avatar_url: str | None = None
    lat: float
    lng: float
    distance_km: float | None = None
    updated_at: datetime


class ProfileUpdate(BaseModel):
    bio: str | None = None
    game_tags: list[str] | None = None
    website: str | None = None
    is_private: bool | None = None
    city: str | None = None
    allow_messages_from: str | None = None
    show_online_status: str | None = None
    allow_friend_requests: bool | None = None


class PublicProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str | None = Field(default=None, validation_alias="full_name")
    username: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    game_tags: list[str] | None = None
    city: str | None = None
    is_private: bool = False
    friends_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    is_friend: bool = False
    friend_request_sent: bool = False
    friend_request_received: bool = False
    is_online: bool = False
    mutual_friends_count: int = 0