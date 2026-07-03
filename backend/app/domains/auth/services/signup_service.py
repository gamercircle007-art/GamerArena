"""Signup flow: WhatsApp OTP verification and account creation."""

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.domains.auth.providers import get_otp_provider
from app.domains.auth.services.otp_store import SignupOTPStore
from app.domains.common.exceptions import ValidationError
from app.domains.user.models import User
from app.domains.user.repository import UserRepository

logger = get_logger(__name__)


class SignupService:
    """Orchestrates signup OTP request and account creation after verification."""

    def __init__(
        self,
        session: AsyncSession,
        redis: aioredis.Redis,
        settings: Settings,
    ) -> None:
        self.settings = settings
        self.user_repo = UserRepository(session)
        self.otp_store = SignupOTPStore(redis, settings)
        self.otp_provider = get_otp_provider(settings)

    async def request_otp(
        self,
        *,
        name: str,
        username: str,
        email: str,
        phone_number: str,
    ) -> None:
        """Validate uniqueness, store signup session, send WhatsApp OTP."""
        phone = UserRepository.normalize_phone(phone_number)
        email_lower = email.lower().strip()
        username_normalized = UserRepository.normalize_username(username)

        if await self.user_repo.username_exists(username_normalized):
            raise ValidationError("This username is already taken")

        if await self.user_repo.email_exists(email_lower):
            raise ValidationError("An account with this email already exists")

        if await self.user_repo.phone_exists(phone):
            raise ValidationError("An account with this phone number already exists")

        otp = await self.otp_store.create_signup_session(
            phone=phone,
            name=name.strip(),
            username=username_normalized,
            email=email_lower,
        )
        await self.otp_provider.send_otp(phone, otp, self.settings.otp_expire_minutes)
        logger.info("signup_otp_sent", phone=phone, email=email_lower)

    async def verify_otp_and_create_user(
        self,
        *,
        phone_number: str,
        otp: str,
        password: str,
    ) -> User:
        """Verify OTP (single-use), hash password, create user account."""
        phone = UserRepository.normalize_phone(phone_number)
        signup_data = await self.otp_store.verify_and_consume(phone, otp)

        if await self.user_repo.username_exists(signup_data["username"]):
            raise ValidationError("This username is already taken")

        if await self.user_repo.email_exists(signup_data["email"]):
            raise ValidationError("An account with this email already exists")

        if await self.user_repo.phone_exists(phone):
            raise ValidationError("An account with this phone number already exists")

        hashed = hash_password(password, self.settings)
        user = await self.user_repo.create_with_password(
            full_name=signup_data["name"],
            username=signup_data["username"],
            email=signup_data["email"],
            phone=phone,
            hashed_password=hashed,
        )
        logger.info("signup_completed", user_id=str(user.id), phone=phone)
        return user