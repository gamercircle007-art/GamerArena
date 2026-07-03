"""Stories API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StoryCreate(BaseModel):
    media_url: str
    media_type: str = Field(pattern="^(image|video)$")
    caption: str | None = None
    privacy: str = "friends"
    duration_seconds: int = 5


class StoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    media_url: str
    media_type: str
    duration_seconds: int
    caption: str | None = None
    privacy: str
    view_count: int
    expires_at: datetime
    created_at: datetime
    viewed: bool = False


class StoryGroupResponse(BaseModel):
    user_id: UUID
    user_name: str | None = None
    user_avatar: str | None = None
    all_viewed: bool = False
    stories: list[StoryResponse]


class StoryViewerResponse(BaseModel):
    user_id: UUID
    name: str | None = None
    avatar_url: str | None = None
    viewed_at: datetime