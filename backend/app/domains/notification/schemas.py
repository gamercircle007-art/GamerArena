"""Notification domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    body: str
    data: dict | None = None
    is_read: bool
    created_at: datetime


class UnreadCountResponse(BaseModel):
    count: int