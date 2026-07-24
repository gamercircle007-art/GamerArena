"""
User domain ORM model.

Fields map to API as:
  full_name  → name
  phone      → phone_number

FUTURE OAUTH:
  Add optional columns: auth_provider (password|google|apple), oauth_provider_id
  Or a separate user_identities table for multiple linked providers per user.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    USER = "user"
    PARLOR_OWNER = "parlor_owner"
    ADMIN = "admin"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Core user entity.

    Account is created only after WhatsApp OTP verification during signup.
    Password is stored as Argon2 hash — never plaintext.
    """

    __tablename__ = "users"

    # Identity
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)

    # Credentials (null for OAuth-only users in future)
    hashed_password: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Profile
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    avatar_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("media_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda roles: [r.value for r in roles]),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
        nullable=False,
    )
    fcm_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    friends_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    followers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    following_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Location (set when user grants permission on any platform)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    location_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} phone={self.phone}>"