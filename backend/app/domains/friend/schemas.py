"""Friend system API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FriendRequestCreate(BaseModel):
    user_id: UUID


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str | None = Field(default=None, validation_alias="full_name")
    username: str | None = None
    avatar_url: str | None = None


class FriendRequestResponse(BaseModel):
    id: UUID
    sender: UserSummary
    created_at: datetime
    status: str = "pending"


class FriendshipResponse(BaseModel):
    id: UUID
    user: UserSummary
    created_at: datetime
    is_online: bool = False


class FriendSuggestion(BaseModel):
    user: UserSummary
    mutual_friends: int = 0


class MutualFriendsResponse(BaseModel):
    count: int
    friends: list[UserSummary]