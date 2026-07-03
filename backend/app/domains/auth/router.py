"""
Auth domain API routes — enterprise signup and login.

| Method | Endpoint                 | Auth | Description                        |
|--------|--------------------------|------|------------------------------------|
| POST   | /auth/signup/request-otp | No   | Send WhatsApp OTP for signup       |
| POST   | /auth/signup/verify-otp  | No   | Verify OTP, set password, register |
| POST   | /auth/login/request-otp  | No   | Send WhatsApp OTP for login        |
| POST   | /auth/login/verify-otp   | No   | Verify OTP and receive JWT         |
| POST   | /auth/login              | No   | Login with username + password     |
| POST   | /auth/refresh-token      | No   | Rotate refresh token               |
| GET    | /auth/me                 | Yes  | Current user profile               |
| POST   | /auth/logout             | Yes  | Revoke refresh token               |

FUTURE ROUTES (scaffolded in providers/oauth/):
  POST /auth/oauth/google   — Google Sign In
  POST /auth/oauth/apple    — Apple Sign In
"""

from typing import Any

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep, SettingsDep
from app.domains.auth.schemas import (
    LoginRequest,
    LoginRequestOtpRequest,
    LoginVerifyOtpRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    SignupRequestOTPRequest,
    SignupVerifyOTPRequest,
    TokenResponse,
)
from app.domains.auth.service import AuthService
from app.domains.user.schemas import UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Invalid credentials or expired token"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit or account lockout"},
    },
)


def _auth_service(db: DbSessionDep, redis: RedisDep, settings: SettingsDep) -> AuthService:
    return AuthService(db, redis, settings)


@router.post(
    "/signup/request-otp",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request signup OTP via WhatsApp",
    description=(
        "Start registration by sending a WhatsApp OTP. "
        "Requires unique email and phone. Rate limited to 5 requests per 10 minutes."
    ),
    response_description="OTP dispatched successfully",
)
async def signup_request_otp(
    body: SignupRequestOTPRequest,
    db: DbSessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> MessageResponse:
    return await _auth_service(db, redis, settings).signup_request_otp(body)


@router.post(
    "/signup/verify-otp",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Verify OTP and create account",
    description=(
        "Complete registration: verify the WhatsApp OTP, set a password, "
        "and receive JWT access + refresh tokens. OTP is single-use."
    ),
    response_description="Account created and tokens issued",
)
async def signup_verify_otp(
    body: SignupVerifyOTPRequest,
    db: DbSessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> TokenResponse:
    return await _auth_service(db, redis, settings).signup_verify_otp(body)


@router.post(
    "/login/request-otp",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request login OTP via WhatsApp",
    description=(
        "Send a WhatsApp OTP to a registered phone number. "
        "Rate limited to 5 requests per 10 minutes."
    ),
)
async def login_request_otp(
    body: LoginRequestOtpRequest,
    db: DbSessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> MessageResponse:
    return await _auth_service(db, redis, settings).login_request_otp(body)


@router.post(
    "/login/verify-otp",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify login OTP",
    description="Verify the WhatsApp OTP and receive JWT access + refresh tokens.",
)
async def login_verify_otp(
    body: LoginVerifyOtpRequest,
    db: DbSessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> TokenResponse:
    return await _auth_service(db, redis, settings).login_verify_otp(body)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with username and password",
    description=(
        "Authenticate with username and password. "
        "Account locks for 15 minutes after 5 failed attempts."
    ),
)
async def login(
    body: LoginRequest,
    db: DbSessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> TokenResponse:
    return await _auth_service(db, redis, settings).login(body)


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new token pair. Old refresh token is invalidated.",
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: DbSessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> TokenResponse:
    return await _auth_service(db, redis, settings).refresh_tokens(body.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
    description="Returns the profile of the user identified by the Bearer access token.",
    responses={200: {"description": "Authenticated user profile"}},
)
async def get_me(current_user: CurrentUserDep) -> UserResponse:
    return current_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and invalidate refresh token",
    description="Revokes the refresh token in Redis. Access token remains valid until expiry.",
)
async def logout(
    body: LogoutRequest,
    db: DbSessionDep,
    redis: RedisDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    _ = current_user
    return await _auth_service(db, redis, settings).logout(body.refresh_token)