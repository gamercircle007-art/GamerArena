"""Redis-backed OTP and signup session storage."""

import json

import redis.asyncio as aioredis

from app.core.config import Settings
from app.domains.common.otp import generate_otp_code, is_dev_bypass_otp
from app.domains.common.exceptions import AuthenticationError, RateLimitError, ValidationError


class SignupOTPStore:
    """Manages signup OTP lifecycle in Redis — single-use, TTL, rate limited."""

    def __init__(self, redis: aioredis.Redis, settings: Settings) -> None:
        self.redis = redis
        self.settings = settings

    def _session_key(self, phone: str) -> str:
        return f"signup:session:{phone}"

    def _rate_key(self, phone: str) -> str:
        return f"signup:otp_rate:{phone}"

    def _generate_otp(self) -> str:
        return generate_otp_code(self.settings)

    async def _enforce_rate_limit(self, phone: str) -> None:
        key = self._rate_key(phone)
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.settings.otp_rate_limit_window_seconds)
        if count > self.settings.otp_rate_limit_count:
            raise RateLimitError(
                f"Too many OTP requests. Maximum {self.settings.otp_rate_limit_count} "
                f"per {self.settings.otp_rate_limit_window_minutes} minutes."
            )

    async def create_signup_session(
        self,
        *,
        phone: str,
        name: str,
        username: str,
        email: str,
    ) -> str:
        """Store pending signup data + OTP. Returns OTP for delivery."""
        await self._enforce_rate_limit(phone)

        otp = self._generate_otp()
        ttl = self.settings.otp_expire_minutes * 60
        payload = {
            "name": name,
            "username": username,
            "email": email.lower(),
            "phone": phone,
            "otp": otp,
            "attempts": 0,
            "consumed": False,
        }
        await self.redis.setex(self._session_key(phone), ttl, json.dumps(payload))
        return otp

    async def verify_and_consume(self, phone: str, submitted_otp: str) -> dict[str, str]:
        """
        Verify OTP (single-use). Returns signup data {name, email, phone}.
        Deletes session on success.
        """
        key = self._session_key(phone)
        raw = await self.redis.get(key)

        if is_dev_bypass_otp(self.settings, submitted_otp):
            if raw is None:
                raise AuthenticationError(
                    "Signup session not found. Please request a new OTP first."
                )
            data = json.loads(raw)
            await self.redis.delete(key)
            return {
                "name": data["name"],
                "username": data["username"],
                "email": data["email"],
                "phone": data["phone"],
            }

        if raw is None:
            raise AuthenticationError("OTP expired or not found. Please request a new one.")

        data = json.loads(raw)
        if data.get("consumed"):
            raise AuthenticationError("OTP already used. Please request a new one.")

        attempts = data.get("attempts", 0)
        if attempts >= self.settings.otp_max_attempts:
            await self.redis.delete(key)
            raise ValidationError("Maximum OTP attempts exceeded. Please request a new OTP.")

        if data.get("otp") != submitted_otp:
            data["attempts"] = attempts + 1
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.setex(key, ttl, json.dumps(data))
            raise AuthenticationError("Invalid OTP. Please try again.")

        await self.redis.delete(key)
        return {
            "name": data["name"],
            "username": data["username"],
            "email": data["email"],
            "phone": data["phone"],
        }


class LoginOTPStore:
    """Manages login OTP lifecycle in Redis — single-use, TTL, rate limited."""

    def __init__(self, redis: aioredis.Redis, settings: Settings) -> None:
        self.redis = redis
        self.settings = settings

    def _session_key(self, phone: str) -> str:
        return f"login:session:{phone}"

    def _rate_key(self, phone: str) -> str:
        return f"login:otp_rate:{phone}"

    def _generate_otp(self) -> str:
        return generate_otp_code(self.settings)

    async def _enforce_rate_limit(self, phone: str) -> None:
        key = self._rate_key(phone)
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.settings.otp_rate_limit_window_seconds)
        if count > self.settings.otp_rate_limit_count:
            raise RateLimitError(
                f"Too many OTP requests. Maximum {self.settings.otp_rate_limit_count} "
                f"per {self.settings.otp_rate_limit_window_minutes} minutes."
            )

    async def create_login_session(self, *, phone: str) -> str:
        """Store login OTP session. Returns OTP for delivery."""
        await self._enforce_rate_limit(phone)

        otp = self._generate_otp()
        ttl = self.settings.otp_expire_minutes * 60
        payload = {
            "phone": phone,
            "otp": otp,
            "attempts": 0,
            "consumed": False,
        }
        await self.redis.setex(self._session_key(phone), ttl, json.dumps(payload))
        return otp

    async def verify_and_consume(self, phone: str, submitted_otp: str) -> str:
        """Verify OTP (single-use). Returns normalized phone on success."""
        key = self._session_key(phone)
        raw = await self.redis.get(key)

        # Dev bypass: accept fixed OTP without a prior Redis session (local only).
        if is_dev_bypass_otp(self.settings, submitted_otp):
            if raw is not None:
                await self.redis.delete(key)
            return phone

        if raw is None:
            raise AuthenticationError("OTP expired or not found. Please request a new one.")

        data = json.loads(raw)
        if data.get("consumed"):
            raise AuthenticationError("OTP already used. Please request a new one.")

        attempts = data.get("attempts", 0)
        if attempts >= self.settings.otp_max_attempts:
            await self.redis.delete(key)
            raise ValidationError("Maximum OTP attempts exceeded. Please request a new OTP.")

        if data.get("otp") != submitted_otp:
            data["attempts"] = attempts + 1
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.setex(key, ttl, json.dumps(data))
            raise AuthenticationError("Invalid OTP. Please try again.")

        await self.redis.delete(key)
        return data["phone"]