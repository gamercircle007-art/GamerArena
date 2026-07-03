"""Like domain Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class LikeCreate(BaseModel):
    target_type: str = Field(..., pattern=r"^(post|comment)$")
    target_id: UUID


class LikeToggleResponse(BaseModel):
    liked: bool
    likes_count: int