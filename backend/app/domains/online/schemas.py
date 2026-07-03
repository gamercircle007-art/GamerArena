"""Online status API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OnlineStatusResponse(BaseModel):
    user_id: UUID
    is_online: bool
    last_seen_at: datetime | None = None
    last_seen_display: str | None = None


class StatusPrivacyUpdate(BaseModel):
    show_to: str = Field(pattern="^(everyone|friends|nobody)$")