from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class OtpRequest(BaseModel):
    phone_number: str


class OtpVerifyRequest(BaseModel):
    phone_number: str
    otp: str = Field(min_length=4, max_length=8)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class UserResponse(BaseModel):
    id: str
    name: str | None
    username: str | None
    email: str | None
    phone_number: str | None
    role: str
    avatar_url: str | None = None
    is_active: bool
    is_verified: bool = True
    email_verified: bool = True
    phone_verified: bool = True
    latitude: float | None = None
    longitude: float | None = None
    city: str | None = None
    country: str | None = None
    location_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    parlor_name: str | None = None
    bookings_count: int | None = None
    likes_count: int | None = None
    following_count: int | None = None
    reviews_count: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 28800
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    limit: int
    has_more: bool