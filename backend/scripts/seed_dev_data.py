#!/usr/bin/env python3
"""Seed local dev data: parlors with locations, tournaments, sample post.

Usage (with docker compose up):
  cd backend && python scripts/seed_dev_data.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_factory
from app.domains.parlor.models import Parlor
from app.domains.post.models import Post
from app.domains.tournament.models import Tournament
from app.domains.user.models import User, UserRole


async def seed(session: AsyncSession) -> None:
    owner_id = uuid.uuid4()
    owner = User(
        id=owner_id,
        full_name="Arena Owner",
        username="arena_owner",
        email="owner@gamercircle.dev",
        phone="+919999999001",
        hashed_password="$argon2id$v=19$m=65536,t=3,p=4$seed$seed",
        role=UserRole.PARLOR_OWNER,
        is_active=True,
        is_verified=True,
    )
    session.add(owner)

    parlors = [
        Parlor(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name="Neon Arena Delhi",
            description="Premium esports lounge in Connaught Place",
            address="Connaught Place, New Delhi",
            location=WKTElement("POINT(77.2167 28.6315)", srid=4326),
            game_types=["BGMI", "Valorant", "CS2"],
            is_verified=True,
            follower_count=120,
        ),
        Parlor(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name="Pixel Pit Gurgaon",
            description="Casual and competitive gaming hub",
            address="Cyber Hub, Gurgaon",
            location=WKTElement("POINT(77.0820 28.4940)", srid=4326),
            game_types=["Valorant", "FIFA"],
            is_verified=False,
            follower_count=45,
        ),
    ]
    session.add_all(parlors)

    now = datetime.now(timezone.utc)
    tournaments = [
        Tournament(
            id=uuid.uuid4(),
            parlor_id=parlors[0].id,
            title="BGMI Weekend Cup",
            game_type="BGMI",
            format="squad",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=4),
            total_slots=16,
            booked_slots=3,
            entry_fee=Decimal("199.00"),
            status="open",
            prizes={"1st": "₹5000", "2nd": "₹3000"},
            rules="No emulators. Standard tournament rules apply.",
        ),
        Tournament(
            id=uuid.uuid4(),
            parlor_id=parlors[1].id,
            title="Valorant 5v5 Open",
            game_type="Valorant",
            format="5v5",
            start_time=now + timedelta(days=5),
            end_time=now + timedelta(days=5, hours=3),
            total_slots=10,
            booked_slots=0,
            entry_fee=Decimal("0"),
            status="open",
        ),
    ]
    session.add_all(tournaments)

    post = Post(
        id=uuid.uuid4(),
        parlor_id=parlors[0].id,
        content="BGMI Weekend Cup registrations are open! Book your slot now.",
        media_urls=[],
    )
    session.add(post)
    parlors[0].post_count = 1

    await session.commit()
    print("Seeded owner:", owner.username)
    for p in parlors:
        print(f"  Parlor: {p.name} ({p.id})")
    for t in tournaments:
        print(f"  Tournament: {t.title} ({t.id})")


async def main() -> None:
    factory = get_session_factory()
    async with factory() as session:
        existing = await session.execute(select(Parlor).limit(1))
        if existing.scalar_one_or_none() is not None:
            print("Parlors already exist — skipping seed.")
            return
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())