"""Auth domain facade — coordinates signup, login, token, and logout services."""

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.domains.auth.schemas import (
    LoginRequest,
    LoginRequestOtpRequest,
    LoginVerifyOtpRequest,
    MessageResponse,
    SignupRequestOTPRequest,
    SignupVerifyOTPRequest,
    TokenResponse,
)
from app.domains.auth.services.login_otp_service import LoginOTPService
from app.domains.auth.services.login_service import LoginService
from app.domains.auth.services.signup_service import SignupService
from app.domains.auth.services.token_service import TokenService
from app.domains.user.repository import UserRepository

logger = get_logger(__name__)


class AuthService:
    """
    Authentication orchestrator.

    MICROSERVICE EXTRACTION: This class becomes the auth microservice core.
    User creation calls would move to user-service via HTTP/gRPC.
    """

    def __init__(
        self,
        session: AsyncSession,
        redis_client: aioredis.Redis,
        settings: Settings,
    ) -> None:
        self.session = session
        self.settings = settings
        self.user_repo = UserRepository(session)
        self.signup_service = SignupService(session, redis_client, settings)
        self.login_service = LoginService(redis_client, settings, self.user_repo)
        self.login_otp_service = LoginOTPService(redis_client, settings, self.user_repo)
        self.token_service = TokenService(redis_client, settings)

    async def signup_request_otp(self, request: SignupRequestOTPRequest) -> MessageResponse:
        await self.signup_service.request_otp(
            name=request.name,
            username=request.username,
            email=str(request.email),
            phone_number=request.phone_number,
        )
        return MessageResponse(
            message="OTP sent to your WhatsApp number. Please verify to complete signup.",
        )

    async def signup_verify_otp(self, request: SignupVerifyOTPRequest) -> TokenResponse:
        user = await self.signup_service.verify_otp_and_create_user(
            phone_number=request.phone_number,
            otp=request.otp,
            password=request.password,
        )
        tokens = await self.token_service.issue_tokens(user)
        return TokenResponse(**tokens)

    async def login_request_otp(self, request: LoginRequestOtpRequest) -> MessageResponse:
        await self.login_otp_service.request_otp(request.phone_number)
        return MessageResponse(
            message="If this phone number is registered, an OTP has been sent to WhatsApp.",
        )

    async def login_verify_otp(self, request: LoginVerifyOtpRequest) -> TokenResponse:
        user = await self.login_otp_service.verify_otp(request.phone_number, request.otp)
        tokens = await self.token_service.issue_tokens(user)
        return TokenResponse(**tokens)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self.login_service.authenticate(request.username, request.password)
        tokens = await self.token_service.issue_tokens(user)
        return TokenResponse(**tokens)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        tokens = await self.token_service.rotate_refresh_token(refresh_token, self.user_repo)
        return TokenResponse(**tokens)

    async def logout(self, refresh_token: str) -> MessageResponse:
        await self.token_service.revoke_by_token_string(refresh_token)
        logger.info("logout_success")
        return MessageResponse(message="Logged out successfully")