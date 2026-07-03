from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.deps import AdminDep, DbDep
from app.models.admin_user import AdminUser
from app.schemas import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    OtpRequest,
    OtpVerifyRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.security import create_access_token, create_refresh_token, decode_token, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


def admin_to_user(admin: AdminUser) -> UserResponse:
    role_name = admin.role.name if admin.role else "admin"
    panel_role = "super_admin" if role_name == "super_admin" else "admin"
    now = datetime.now(UTC)
    return UserResponse(
        id=admin.id,
        name=admin.name,
        username=admin.username,
        email=admin.email,
        phone_number=admin.phone or "+919999999999",
        role=panel_role,
        avatar_url=admin.avatar_url,
        is_active=admin.is_active,
        is_verified=True,
        email_verified=True,
        phone_verified=True,
        created_at=admin.created_at or now,
        updated_at=admin.last_login or admin.created_at or now,
    )


def token_response(admin: AdminUser) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(admin.id),
        refresh_token=create_refresh_token(admin.id),
        expires_in=settings.ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=admin_to_user(admin),
    )


async def _find_admin(db, username: str) -> AdminUser | None:
    result = await db.execute(
        select(AdminUser)
        .options(selectinload(AdminUser.role))
        .where(or_(AdminUser.username == username, AdminUser.email == username))
    )
    return result.scalar_one_or_none()


async def _find_admin_by_phone(db, phone: str) -> AdminUser | None:
    result = await db.execute(
        select(AdminUser)
        .options(selectinload(AdminUser.role))
        .where(AdminUser.phone == phone)
    )
    return result.scalar_one_or_none()


async def _find_admin_by_id(db, admin_id: str) -> AdminUser | None:
    result = await db.execute(
        select(AdminUser)
        .options(selectinload(AdminUser.role))
        .where(AdminUser.id == admin_id)
    )
    return result.scalar_one_or_none()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DbDep) -> TokenResponse:
    admin = await _find_admin(db, body.username)
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    admin.last_login = datetime.now(UTC)
    await db.commit()
    await db.refresh(admin)
    return token_response(admin)


@router.post("/login/request-otp", response_model=MessageResponse)
async def request_otp(body: OtpRequest, db: DbDep) -> MessageResponse:
    admin = await _find_admin_by_phone(db, body.phone_number)
    if not admin:
        return MessageResponse(message="If this phone number is registered, an OTP has been sent.", success=True)
    return MessageResponse(message="OTP sent. Use dev code 123456 in local environment.", success=True)


@router.post("/login/verify-otp", response_model=TokenResponse)
async def verify_otp(body: OtpVerifyRequest, db: DbDep) -> TokenResponse:
    if body.otp != settings.OTP_DEV_BYPASS_CODE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    admin = await _find_admin_by_phone(db, body.phone_number)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone or OTP")

    admin.last_login = datetime.now(UTC)
    await db.commit()
    await db.refresh(admin)
    return token_response(admin)


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest, db: DbDep) -> TokenResponse:
    payload = decode_token(body.refresh_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    admin = await _find_admin_by_id(db, payload["sub"])
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return token_response(admin)


@router.get("/me", response_model=UserResponse)
async def me(admin: AdminDep) -> UserResponse:
    return admin_to_user(admin)


@router.post("/logout", response_model=MessageResponse)
async def logout(_: LogoutRequest) -> MessageResponse:
    return MessageResponse(message="Logged out successfully")