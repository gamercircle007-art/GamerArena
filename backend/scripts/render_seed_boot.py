"""Best-effort boot seed for Render. Never raises to shell (exits 0/1 only)."""
from __future__ import annotations

import asyncio
import os
import runpy
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.config import get_settings  # noqa: E402


async def need_full_seed() -> bool:
    if os.environ.get("FORCE_SEED") == "1":
        return True
    eng = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        async with eng.connect() as conn:
            try:
                n = await conn.scalar(text("SELECT COUNT(*) FROM gaming_places"))
            except Exception:
                return False
            return int(n or 0) == 0
    finally:
        await eng.dispose()


async def ensure_admin_only() -> None:
    from sqlalchemy import select

    from app.core.security import hash_password
    from app.db import session as db_session
    import app.db.models  # noqa: F401
    from app.domains.user.models import User, UserRole

    db_session._engine = None
    db_session._session_factory = None
    factory = db_session.get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        if user is None:
            session.add(
                User(
                    full_name="GameConnect Admin",
                    username="admin",
                    email="admin@gameconnect.in",
                    phone="+919999999999",
                    hashed_password=hash_password("Admin@123"),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                    email_verified=True,
                    phone_verified=True,
                )
            )
            await session.commit()
            print("Admin user created: admin / Admin@123")
            return
        if user.role != UserRole.ADMIN or not user.is_active:
            user.role = UserRole.ADMIN
            user.is_active = True
            await session.commit()
            print("Admin role/active repaired")
        else:
            print("Admin user already present")


async def main() -> None:
    try:
        await ensure_admin_only()
    except Exception as exc:  # noqa: BLE001
        print(f"ensure_admin failed (non-fatal): {exc}")
    try:
        if await need_full_seed():
            print("Empty gaming_places — running seed_render_bootstrap...")
            runpy.run_path(str(BACKEND_ROOT / "scripts" / "seed_render_bootstrap.py"), run_name="__main__")
        else:
            print("skip full seed")
    except Exception as exc:  # noqa: BLE001
        print(f"full seed failed (non-fatal): {exc}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        print(f"seed boot failed: {exc}")
        sys.exit(1)
