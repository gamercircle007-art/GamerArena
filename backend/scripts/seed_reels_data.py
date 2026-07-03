#!/usr/bin/env python3
"""Seed demo users and reels with placeholder videos.

Usage:
  cd backend && python scripts/seed_reels_data.py
"""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session_factory
from app.domains.reel.models import Reel
from app.domains.user.models import User

DEMO_VIDEOS = [
    (
        "Epic BGMI clutch in final circle",
        "#bgmi #esports #clutch",
        "Neon Arena Delhi",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ForBiggerBlazes.jpg",
    ),
    (
        "Valorant ace on Ascent — full team wipe",
        "#valorant #gaming #ace",
        "Cyber Hub Gurgaon",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ForBiggerEscapes.jpg",
    ),
    (
        "Weekend tournament highlights at our cafe",
        "#tournament #gamingcafe",
        "Mumbai",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ForBiggerFun.jpg",
    ),
    (
        "Pro gaming setup tour — RGB everything",
        "#setup #pcgaming #rgb",
        "Bangalore",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ForBiggerJoyrides.jpg",
    ),
    (
        "Controller review: best paddles for FPS",
        "#controller #review #fps",
        "Chennai",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ForBiggerMeltdowns.jpg",
    ),
    (
        "Console gaming night at the parlor",
        "#console #ps5 #xbox",
        "Hyderabad",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/Sintel.jpg",
    ),
]

DEMO_USERS = [
    ("pro_gamer_raj", "Raj Sharma", "+919999999101"),
    ("valorant_queen", "Priya Nair", "+919999999102"),
    ("cafe_host_arjun", "Arjun Mehta", "+919999999103"),
    ("setup_guru", "Dev Patel", "+919999999104"),
]


async def seed(session: AsyncSession) -> None:
    users: list[User] = []
    for username, name, phone in DEMO_USERS:
        existing = await session.execute(select(User).where(User.username == username))
        user = existing.scalar_one_or_none()
        if user is None:
            user = User(
                id=uuid.uuid4(),
                username=username,
                full_name=name,
                phone=phone,
                email=f"{username}@gamercircle.dev",
                hashed_password="$argon2id$v=19$m=65536,t=3,p=4$seed$seed",
                is_active=True,
                is_verified=True,
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/png?seed={username}",
            )
            session.add(user)
        users.append(user)

    await session.flush()

    for i, (caption, tags, location, video, thumb) in enumerate(DEMO_VIDEOS):
        user = users[i % len(users)]
        existing = await session.execute(
            select(Reel).where(Reel.caption == caption, Reel.user_id == user.id)
        )
        if existing.scalar_one_or_none():
            continue
        reel = Reel(
            id=uuid.uuid4(),
            user_id=user.id,
            video_url=video,
            thumbnail_url=thumb,
            cover_url=thumb,
            caption=caption,
            hashtags=[t.lstrip("#") for t in tags.split() if t.startswith("#")],
            location=location,
            duration_seconds=15 + (i % 10),
            width=1080,
            height=1920,
            aspect_ratio="9:16",
            filter_name=["normal", "cinema", "warm", "cool"][i % 4],
            music_title="Neon Pulse",
            privacy="public",
            likes_count=120 + i * 37,
            views_count=800 + i * 210,
            comments_count=12 + i,
        )
        session.add(reel)

    await session.commit()
    print("Seeded demo reel users and reels.")


async def main() -> None:
    factory = get_session_factory()
    async with factory() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())