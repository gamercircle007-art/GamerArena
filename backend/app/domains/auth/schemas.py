"""Auth domain request/response schemas with strict validation and OpenAPI examples."""

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domains.user.schemas import UserResponse

_PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,128}$")
_PASSWORD_DESCRIPTION = (
    "Min 6 characters with at least one uppercase letter, one lowercase letter, and one digit"
)
_USERNAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{2,29}$")


class SignupRequestOTPRequest(BaseModel):
    """Step 1: Provide name, username, email, phone — receive WhatsApp OTP."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Jane Doe",
                    "username": "janedoe",
                    "email": "jane@example.com",
                    "phone_number": "+919876543210",
                }
            ]
        }
    )

    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Unique handle (letters, numbers, underscore; starts with a letter)",
        examples=["janedoe"],
    )
    email: EmailStr = Field(..., description="Unique email address")
    phone_number: str = Field(
        ...,
        pattern=r"^\+?[1-9]\d{6,14}$",
        description="E.164 phone number (e.g. +919876543210)",
        examples=["+919876543210"],
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not _USERNAME_PATTERN.match(value):
            raise ValueError(
                "Username must be 3-30 characters, start with a letter, "
                "and contain only letters, numbers, and underscores"
            )
        return value


class SignupVerifyOTPRequest(BaseModel):
    """Step 2: Verify OTP and set password — account is created."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "phone_number": "+919876543210",
                    "otp": "123456",
                    "password": "SecurePass1",
                }
            ]
        }
    )

    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{6,14}$")
    otp: str = Field(..., min_length=4, max_length=8, pattern=r"^\d+$", description="6-digit OTP")
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description=_PASSWORD_DESCRIPTION,
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not _PASSWORD_PATTERN.match(value):
            raise ValueError(
                "Password must be 6-128 characters with at least one uppercase, "
                "one lowercase, and one digit"
            )
        return value


class LoginRequestOtpRequest(BaseModel):
    """Step 1: Request WhatsApp OTP for login."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"phone_number": "+919876543210"}]
        }
    )

    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{6,14}$")


class LoginVerifyOtpRequest(BaseModel):
    """Step 2: Verify login OTP and receive JWT tokens."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"phone_number": "+919876543210", "otp": "123456"}
            ]
        }
    )

    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{6,14}$")
    otp: str = Field(..., min_length=4, max_length=8, pattern=r"^\d+$", description="6-digit OTP")


class LoginRequest(BaseModel):
    """Login with username *or* phone + password."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"username": "janedoe", "password": "SecurePass1"},
                {"username": "+919999999010", "password": "Demo@123"},
            ]
        }
    )

    # Accepts handle (janedoe) or E.164 / 10-digit phone (+9199… / 9999999010)
    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="Username handle or phone number",
    )
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_login_identifier(cls, value: str) -> str:
        raw = value.strip()
        if not raw:
            raise ValueError("Username or phone is required")
        # Phone: +E.164 or bare digits (10–15)
        digits = "".join(c for c in raw if c.isdigit())
        if raw.startswith("+") or (digits and len(digits) >= 10 and raw.replace("+", "").replace(" ", "").isdigit()):
            if len(digits) < 10 or len(digits) > 15:
                raise ValueError("Phone number must be 10–15 digits")
            return raw
        if not _USERNAME_PATTERN.match(raw):
            raise ValueError(
                "Username must be 3-30 characters, start with a letter, "
                "and contain only letters, numbers, and underscores — "
                "or use a valid phone number"
            )
        return raw


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}]
        }
    )

    refresh_token: str = Field(..., min_length=10)


class LogoutRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}]
        }
    )

    refresh_token: str = Field(..., min_length=10)


class TokenResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJ...",
                    "refresh_token": "eyJ...",
                    "token_type": "bearer",
                    "expires_in": 1800,
                    "user": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Jane Doe",
                        "username": "janedoe",
                        "email": "jane@example.com",
                        "phone_number": "+919876543210",
                        "is_active": True,
                        "is_verified": True,
                        "email_verified": True,
                        "phone_verified": True,
                        "created_at": "2026-06-24T12:00:00Z",
                        "updated_at": "2026-06-24T12:00:00Z",
                    },
                }
            ]
        }
    )

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")
    user: UserResponse


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "OTP sent to your WhatsApp number.",
                    "success": True,
                }
            ]
        }
    )

    message: str
    success: bool = True