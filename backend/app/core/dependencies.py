"""
FastAPI dependency injection wiring.

Central place for shared dependencies (DB session, Redis, current user).
When splitting into microservices, each service will have its own dependency module
but can share patterns from here.
"""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.db.session import get_db_session
from app.domains.user.repository import UserRepository
from app.domains.user.schemas import UserResponse

security_scheme = HTTPBearer(auto_error=False)

# Type aliases for cleaner route signatures
SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_redis_client(
    settings: SettingsDep,
) -> AsyncGenerator[aioredis.Redis, None]:
    """Provide an async Redis client per request."""
    client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.aclose()


RedisDep = Annotated[aioredis.Redis, Depends(get_redis_client)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: DbSessionDep,
    settings: SettingsDep,
) -> UserResponse:
    """
    Resolve the authenticated user from JWT Bearer token.
    Raises 401 if token is missing, invalid, or user not found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = decode_token(credentials.credentials, settings)
    if token_payload is None or token_payload.token_type != TOKEN_TYPE_ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(UUID(token_payload.sub))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse.model_validate(user)


CurrentUserDep = Annotated[UserResponse, Depends(get_current_user)]


async def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: DbSessionDep,
    settings: SettingsDep,
) -> UserResponse | None:
    """Return current user if authenticated, otherwise None."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db, settings)
    except HTTPException:
        return None


OptionalCurrentUserDep = Annotated[UserResponse | None, Depends(get_optional_current_user)]