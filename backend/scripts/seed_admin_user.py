#!/usr/bin/env python3
"""Create or update the local dev admin account.

Usage:
  cd backend && python scripts/seed_admin_user.py

Credentials (local dev only):
  Username: admin
  Password: Admin@123
  Phone OTP: +919999999999 / OTP 123456 (when OTP_DEV_BYPASS_CODE is set in run_dev.py)
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test_jwt_secret_key_for_local_development_only_32chars",
)
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BACKEND_ROOT / 'dev.db'}",
)

from sqlalchemy import select

from app.core.security import hash_password
from app.db import session as db_session
from app.db.base import Base
import app.db.models  # noqa: F401
from app.domains.user.models import User, UserRole

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"
ADMIN_EMAIL = "admin@gameconnect.in"
ADMIN_PHONE = "+919999999999"
ADMIN_NAME = "GameConnect Admin"


async def seed_admin() -> None:
    db_session.get_settings.cache_clear() if hasattr(db_session, "get_settings") else None
    db_session._engine = None
    db_session._session_factory = None

    engine = db_session.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = db_session.get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(User).where(User.username == ADMIN_USERNAME)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                full_name=ADMIN_NAME,
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                phone=ADMIN_PHONE,
                hashed_password=hash_password(ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                email_verified=True,
                phone_verified=True,
            )
            session.add(user)
            action = "created"
        else:
            user.full_name = ADMIN_NAME
            user.email = ADMIN_EMAIL
            user.phone = ADMIN_PHONE
            user.hashed_password = hash_password(ADMIN_PASSWORD)
            user.role = UserRole.ADMIN
            user.is_active = True
            user.is_verified = True
            user.email_verified = True
            user.phone_verified = True
            action = "updated"

        await session.commit()
        print(f"Admin user {action}.")
        print(f"  Username: {ADMIN_USERNAME}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print(f"  Phone:    {ADMIN_PHONE}")
        print(f"  Email:    {ADMIN_EMAIL}")
        print(f"  Role:     {UserRole.ADMIN.value}")


if __name__ == "__main__":
    asyncio.run(seed_admin())