"""
Reusable OTP generation, storage, and verification logic.

OTPs are stored in Redis with TTL. Channel-agnostic — used by both email and WhatsApp flows.
When auth becomes a microservice, this module moves with the auth domain.
"""

import json
import secrets
from enum import StrEnum

import redis.asyncio as aioredis

from app.core.config import Settings
from app.domains.common.exceptions import AuthenticationError, RateLimitError, ValidationError


def generate_otp_code(settings: Settings) -> str:
    """Return fixed dev OTP when configured, otherwise a secure random code."""
    if settings.use_otp_dev_bypass:
        return settings.otp_dev_bypass_code
    return "".join(str(secrets.randbelow(10)) for _ in range(settings.otp_length))


def is_dev_bypass_otp(settings: Settings, submitted_otp: str) -> bool:
    """True when submitted OTP matches the configured dev bypass code."""
    return settings.use_otp_dev_bypass and submitted_otp == settings.otp_dev_bypass_code


class OTPChannel(StrEnum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class OTPService:
    """Handles OTP lifecycle in Redis."""

    def __init__(self, redis_client: aioredis.Redis, settings: Settings) -> None:
        self.redis = redis_client
        self.settings = settings

    def _otp_key(self, channel: OTPChannel, identifier: str) -> str:
        return f"otp:{channel.value}:{identifier}"

    def _rate_limit_key(self, channel: OTPChannel, identifier: str) -> str:
        return f"otp:rate:{channel.value}:{identifier}"

    def _generate_otp(self) -> str:
        return generate_otp_code(self.settings)

    async def _check_rate_limit(self, channel: OTPChannel, identifier: str) -> None:
        """Enforce hourly OTP request rate limit per identifier."""
        key = self._rate_limit_key(channel, identifier)
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 3600)
        if count > self.settings.otp_rate_limit_per_hour:
            raise RateLimitError(
                f"OTP request limit exceeded. Try again later. "
                f"(max {self.settings.otp_rate_limit_per_hour}/hour)"
            )

    async def create_and_store(
        self,
        channel: OTPChannel,
        identifier: str,
    ) -> str:
        """
        Generate OTP, store in Redis with TTL, return the OTP (for delivery).
        In production, never log or return OTP in API responses — only send via channel.
        """
        await self._check_rate_limit(channel, identifier)

        otp = self._generate_otp()
        key = self._otp_key(channel, identifier)
        ttl_seconds = self.settings.otp_expire_minutes * 60

        payload = json.dumps({
            "otp": otp,
            "attempts": 0,
            "verified": False,
        })
        await self.redis.setex(key, ttl_seconds, payload)
        return otp

    async def verify(
        self,
        channel: OTPChannel,
        identifier: str,
        submitted_otp: str,
    ) -> bool:
        """
        Verify submitted OTP. Increments attempt counter.
        Raises ValidationError on max attempts; AuthenticationError on mismatch.
        """
        key = self._otp_key(channel, identifier)
        raw = await self.redis.get(key)

        if raw is None:
            raise AuthenticationError("OTP expired or not found. Please request a new one.")

        data = json.loads(raw)
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

        # Mark as verified but keep key briefly for login step
        data["verified"] = True
        ttl = await self.redis.ttl(key)
        if ttl > 0:
            await self.redis.setex(key, ttl, json.dumps(data))
        return True

    async def is_verified(self, channel: OTPChannel, identifier: str) -> bool:
        """Check if OTP was successfully verified (used before issuing JWT)."""
        key = self._otp_key(channel, identifier)
        raw = await self.redis.get(key)
        if raw is None:
            return False
        data = json.loads(raw)
        return data.get("verified", False)

    async def consume_verification(self, channel: OTPChannel, identifier: str) -> None:
        """Remove OTP from Redis after successful login."""
        await self.redis.delete(self._otp_key(channel, identifier))