#!/usr/bin/env python3
"""Bootstrap demo venues + users for empty Render/staging DBs.

Runs after migrations when gaming_places is empty (or FORCE_SEED=1).
Safe to re-run: users upsert by phone; places upsert by google_place_id.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

# Ensure settings can load if JWT only set in env on Render
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "bootstrap_jwt_secret_key_for_render_seed_only_32c",
)

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session as db_session
import app.db.models  # noqa: F401
from app.domains.gaming_place.models import GamingPlace
from app.domains.user.models import User, UserRole
from app.core.security import hash_password


DEMO_PLACES = [
    {
        "name": "Neon Arena Cyber Cafe",
        "address": "Connaught Place, New Delhi",
        "lat": 28.6315,
        "lng": 77.2167,
        "city": "Delhi",
        "image": "https://picsum.photos/id/1015/800/600",
        "rating": 4.6,
    },
    {
        "name": "Pixel Pit Gaming Lounge",
        "address": "Saket, New Delhi",
        "lat": 28.5245,
        "lng": 77.2066,
        "city": "Delhi",
        "image": "https://picsum.photos/id/1016/800/600",
        "rating": 4.4,
    },
    {
        "name": "Apex Room Esports",
        "address": "Sector 18, Noida",
        "lat": 28.5708,
        "lng": 77.3210,
        "city": "Noida",
        "image": "https://picsum.photos/id/1018/800/600",
        "rating": 4.7,
    },
    {
        "name": "Ghaziabad Game Hub",
        "address": "Indirapuram, Ghaziabad",
        "lat": 28.6415,
        "lng": 77.3645,
        "city": "Ghaziabad",
        "image": "https://picsum.photos/id/1025/800/600",
        "rating": 4.3,
    },
    {
        "name": "Gurgaon Battle Station",
        "address": "Cyber Hub, Gurugram",
        "lat": 28.4950,
        "lng": 77.0890,
        "city": "Gurgaon",
        "image": "https://picsum.photos/id/1031/800/600",
        "rating": 4.5,
    },
    {
        "name": "Delhi VR Zone",
        "address": "Rajouri Garden, New Delhi",
        "lat": 28.6450,
        "lng": 77.1200,
        "city": "Delhi",
        "image": "https://picsum.photos/id/1040/800/600",
        "rating": 4.2,
    },
]


async def ensure_places(session: AsyncSession) -> int:
    count = (
        await session.execute(select(func.count()).select_from(GamingPlace))
    ).scalar_one()
    if count and count > 0 and os.environ.get("FORCE_SEED") != "1":
        print(f"gaming_places already has {count} rows — skip place seed")
        return int(count)

    city_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    created = 0
    for i, p in enumerate(DEMO_PLACES):
        gpid = f"demo-render-{i+1}"
        existing = (
            await session.execute(
                select(GamingPlace).where(GamingPlace.google_place_id == gpid)
            )
        ).scalar_one_or_none()
        if existing:
            continue
        place = GamingPlace(
            id=uuid.uuid4(),
            google_place_id=gpid,
            name=p["name"],
            address=p["address"],
            city_id=city_id,
            latitude=p["lat"],
            longitude=p["lng"],
            rating=p["rating"],
            user_ratings_total=120 + i * 17,
            phone=f"+91110000000{i}",
            business_status="OPERATIONAL",
            primary_type="gaming_cafe",
            types=["gaming_cafe", "point_of_interest"],
            image_url=p["image"],
            photos=[{"url": p["image"]}],
            raw_data={"city": p["city"], "source": "seed_render_bootstrap"},
            created_at=now,
            updated_at=now,
        )
        session.add(place)
        created += 1
    await session.commit()
    print(f"Created {created} demo gaming_places")
    return created


async def ensure_admin(session: AsyncSession) -> None:
    """Always upsert platform admin (needed for Angular admin panel)."""
    from sqlalchemy import select

    admin_username = "admin"
    admin_password = "Admin@123"
    admin_phone = "+919999999999"
    admin_email = "admin@gameconnect.in"

    result = await session.execute(select(User).where(User.username == admin_username))
    user = result.scalar_one_or_none()
    if user is None:
        # phone unique — clear collision if any
        phone_hit = (
            await session.execute(select(User).where(User.phone == admin_phone))
        ).scalar_one_or_none()
        if phone_hit is not None:
            phone_hit.username = admin_username
            phone_hit.role = UserRole.ADMIN
            phone_hit.hashed_password = hash_password(admin_password)
            phone_hit.is_active = True
            phone_hit.is_verified = True
            phone_hit.email_verified = True
            phone_hit.phone_verified = True
            phone_hit.email = admin_email
            phone_hit.full_name = "GameConnect Admin"
            await session.commit()
            print("Admin promoted from existing phone user")
            return
        session.add(
            User(
                full_name="GameConnect Admin",
                username=admin_username,
                email=admin_email,
                phone=admin_phone,
                hashed_password=hash_password(admin_password),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                email_verified=True,
                phone_verified=True,
            )
        )
        await session.commit()
        print("Admin user created: admin / Admin@123")
    else:
        user.role = UserRole.ADMIN
        user.hashed_password = hash_password(admin_password)
        user.is_active = True
        user.is_verified = True
        user.email_verified = True
        user.phone_verified = True
        user.phone = admin_phone
        user.email = admin_email
        await session.commit()
        print("Admin user ensured: admin / Admin@123")


async def main() -> None:
    # reset engine so DATABASE_URL from env is used
    db_session._engine = None  # type: ignore[attr-defined]
    db_session._session_factory = None  # type: ignore[attr-defined]

    factory = db_session.get_session_factory()
    async with factory() as session:
        await ensure_places(session)
        await ensure_admin(session)

    # Full demo users/posts/bookings
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "seed_demo_full", BACKEND_ROOT / "scripts" / "seed_demo_full.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    async with factory() as session:
        await mod.seed(session)
        # Re-ensure admin after full seed (in case seed overwrote)
        await ensure_admin(session)

    print("Bootstrap complete.")
    print("  User:  +919999999010 / Demo@123  (or username lens_by_manish)")
    print("  Admin: admin / Admin@123  (phone +919999999999)")
    print("  OTP bypass only when APP_ENV!=prod and OTP_DEV_BYPASS_CODE set")


if __name__ == "__main__":
    asyncio.run(main())
