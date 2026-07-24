"""Phone + password login with brute-force protection."""

import redis.asyncio as aioredis

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.security import verify_password
from app.domains.common.exceptions import AuthenticationError, RateLimitError
from app.domains.user.models import User
from app.domains.user.repository import UserRepository

logger = get_logger(__name__)


class LoginService:
    """Handles credential-based login with Redis-backed lockout."""

    def __init__(
        self,
        redis: aioredis.Redis,
        settings: Settings,
        user_repo: UserRepository,
    ) -> None:
        self.redis = redis
        self.settings = settings
        self.user_repo = user_repo

    def _attempts_key(self, username: str) -> str:
        return f"auth:login_attempts:{username}"

    def _lockout_key(self, username: str) -> str:
        return f"auth:login_lockout:{username}"

    async def _is_locked_out(self, username: str) -> bool:
        return await self.redis.exists(self._lockout_key(username)) > 0

    async def _record_failed_attempt(self, username: str) -> None:
        key = self._attempts_key(username)
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.settings.login_lockout_minutes * 60)

        if count >= self.settings.login_max_attempts:
            await self.redis.setex(
                self._lockout_key(username),
                self.settings.login_lockout_minutes * 60,
                "1",
            )
            await self.redis.delete(key)
            logger.warning("account_locked", username=username)
            raise RateLimitError(
                f"Account temporarily locked due to too many failed attempts. "
                f"Try again in {self.settings.login_lockout_minutes} minutes."
            )

    async def _clear_attempts(self, username: str) -> None:
        await self.redis.delete(self._attempts_key(username))

    @staticmethod
    def _looks_like_phone(identifier: str) -> bool:
        raw = identifier.strip()
        digits = "".join(c for c in raw if c.isdigit())
        if not digits or len(digits) < 10:
            return False
        stripped = raw.replace("+", "").replace(" ", "").replace("-", "")
        return stripped.isdigit() or raw.startswith("+")

    async def authenticate(self, username: str, password: str) -> User:
        """Verify username *or* phone + password. Raises AuthenticationError on failure."""
        raw = username.strip()
        # Lockout key: phone-normalized or username-normalized
        if self._looks_like_phone(raw):
            lock_key = UserRepository.normalize_phone(raw)
        else:
            lock_key = UserRepository.normalize_username(raw)

        if await self._is_locked_out(lock_key):
            logger.warning("login_blocked_lockout", username=lock_key)
            raise RateLimitError(
                "Account temporarily locked. Please try again later."
            )

        if self._looks_like_phone(raw):
            user = await self.user_repo.get_by_phone(raw)
        else:
            user = await self.user_repo.get_by_username(raw)

        # Generic message — never reveal whether username/phone exists
        invalid_msg = "Invalid username or password"

        if user is None or not user.is_active or not user.hashed_password:
            await self._record_failed_attempt(lock_key)
            logger.warning(
                "login_failed",
                username=lock_key,
                reason="user_not_found_or_inactive",
            )
            raise AuthenticationError(invalid_msg)

        if not verify_password(password, user.hashed_password, self.settings):
            await self._record_failed_attempt(lock_key)
            logger.warning("login_failed", username=lock_key, reason="invalid_password")
            raise AuthenticationError(invalid_msg)

        await self._clear_attempts(lock_key)
        logger.info(
            "login_success",
            user_id=str(user.id),
            username=user.username,
        )
        return user