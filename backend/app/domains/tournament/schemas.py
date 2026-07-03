"""Tournament domain Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.parlor.schemas import ParlorSummary


class TournamentCreate(BaseModel):
    """Payload for creating a tournament (parlor resolved from owner)."""

    title: str = Field(..., min_length=3, max_length=255)
    game_type: str = Field(..., min_length=2, max_length=50)
    format: str = Field(..., min_length=2, max_length=50)
    start_time: datetime
    end_time: datetime
    total_slots: int = Field(..., ge=1, le=500)
    entry_fee: Decimal = Field(default=Decimal("0"), ge=0)
    prizes: dict[str, str] | None = None
    rules: str | None = Field(default=None, max_length=5000)

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, end_time: datetime, info) -> datetime:
        start_time = info.data.get("start_time")
        if start_time is not None and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class TournamentUpdate(BaseModel):
    """Partial update for a tournament."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    game_type: str | None = Field(default=None, min_length=2, max_length=50)
    format: str | None = Field(default=None, min_length=2, max_length=50)
    start_time: datetime | None = None
    end_time: datetime | None = None
    total_slots: int | None = Field(default=None, ge=1, le=500)
    entry_fee: Decimal | None = Field(default=None, ge=0)
    prizes: dict[str, str] | None = None
    rules: str | None = Field(default=None, max_length=5000)
    status: str | None = Field(default=None, pattern=r"^(draft|open|full|live|completed|cancelled)$")


class TournamentResponse(BaseModel):
    """Public tournament detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parlor_id: UUID
    parlor: ParlorSummary
    title: str
    game_type: str
    format: str
    start_time: datetime
    end_time: datetime
    total_slots: int
    booked_slots: int
    entry_fee: Decimal
    prizes: dict | None = None
    rules: str | None = None
    status: str
    is_booked_by_me: bool = False
    created_at: datetime
    updated_at: datetime