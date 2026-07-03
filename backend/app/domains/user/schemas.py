"""User domain Pydantic schemas (API contracts)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domains.user.models import UserRole


_USERNAME_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_]{2,29}$"


class UserBase(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, pattern=r"^\+?[1-9]\d{6,14}$")
    name: str | None = Field(default=None, min_length=2, max_length=100)
    username: str | None = Field(default=None, pattern=_USERNAME_PATTERN)


class UserCreate(UserBase):
    pass


class UserLocationUpdate(BaseModel):
    """GPS coordinates and optional reverse-geocoded place info."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code",
    )


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    username: str | None = Field(default=None, pattern=_USERNAME_PATTERN)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, pattern=r"^\+?[1-9]\d{6,14}$")


class UserResponse(BaseModel):
    """
    Public user profile returned by /auth/me and token responses.

    Serializes ORM fields full_name → name, phone → phone_number.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str | None = Field(validation_alias="full_name")
    username: str | None = None
    email: str | None = None
    phone_number: str | None = Field(validation_alias="phone")
    role: UserRole = UserRole.USER
    avatar_url: str | None = None
    is_active: bool
    is_verified: bool
    email_verified: bool
    phone_verified: bool
    latitude: float | None = None
    longitude: float | None = None
    city: str | None = None
    country: str | None = None
    location_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("name", mode="before")
    @classmethod
    def accept_full_name(cls, value: str | None, info) -> str | None:
        return value