"""Booking domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BookingResponse(BaseModel):
    """Booking returned after book/cancel/list operations."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tournament_id: UUID
    user_id: UUID
    slot_number: int
    status: str
    payment_status: str
    created_at: datetime