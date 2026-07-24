"""Admin panel Pydantic request/response schemas."""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AdminParlorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=500)
    address: str | None = Field(default=None, max_length=2000)
    phone: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    primary_type: str | None = Field(default="gaming", max_length=100)
    game_types: list[str] = Field(default_factory=list, max_length=20)
    owner_id: UUID | None = None
    is_verified: bool = False
    is_active: bool = True
    price_per_hour: Decimal | None = Field(default=None, ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    opening_hours: dict | None = None
    city_id: UUID | None = None


class AdminParlorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=500)
    address: str | None = Field(default=None, max_length=2000)
    phone: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    primary_type: str | None = Field(default=None, max_length=100)
    game_types: list[str] | None = Field(default=None, max_length=20)
    owner_id: UUID | None = None
    is_verified: bool | None = None
    is_active: bool | None = None
    price_per_hour: Decimal | None = Field(default=None, ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    opening_hours: dict | None = None
    business_status: str | None = Field(default=None, max_length=50)


class AdminParlorVerify(BaseModel):
    is_verified: bool


class AdminAssignOwner(BaseModel):
    owner_id: UUID | None = None
    promote_to_owner: bool = True


class AdminUserPatch(BaseModel):
    is_active: bool | None = None
    role: str | None = None
    is_verified: bool | None = None


class AdminTournamentStatus(BaseModel):
    status: str = Field(..., min_length=2, max_length=30)


class AdminBroadcastRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    target: str = Field(default="everyone", max_length=50)
    type: str = Field(default="info", max_length=30)


class AdminOfferUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    discount_amount: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    max_uses: int | None = Field(default=None, ge=1)


class AdminSlotUpdate(BaseModel):
    slot_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    price_per_hour: Decimal | None = Field(default=None, gt=0)
    original_price: Decimal | None = Field(default=None, gt=0)
    max_players: int | None = Field(default=None, ge=1, le=50)
    is_available: bool | None = None


class AdminBookingStatusPatch(BaseModel):
    booking_status: str | None = Field(default=None, max_length=40)
    payment_status: str | None = Field(default=None, max_length=40)
