"""Comment domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommentUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = Field(validation_alias="full_name")
    avatar_url: str | None = None


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: UUID | None = None


class CommentResponse(BaseModel):
    id: UUID
    user: CommentUserSummary
    content: str
    parent_id: UUID | None
    likes_count: int
    is_liked: bool = False
    is_deleted: bool
    reply_count: int = 0
    created_at: datetime