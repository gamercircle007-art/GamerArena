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