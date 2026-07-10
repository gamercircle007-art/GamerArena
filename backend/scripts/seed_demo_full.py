#!/usr/bin/env python3
"""
Full demo data seeder for Paythan / GameConnect.

Makes the app fully demo-ready with realistic Delhi gaming data.

Usage (from backend dir):
  PYTHONPATH=. .venv/bin/python scripts/seed_demo_full.py

Or with Postgres if DATABASE_URL set.

Creates:
- 6 demo users (login with phone + Demo@123)
- Uses existing gaming_places for venues
- 6+ gaming_place_extensions (prices, verified, owners)
- 6 bookings (upcoming/completed/cancelled)
- 6 posts with picsum images
- 5 reels with public playable video urls + demo metadata (5s)
- 3 conversations + messages
- Some follows, likes etc for realism

After run, login with e.g. +919999999010 / Demo@123
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
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

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db import session as db_session
from app.db.base import Base
import app.db.models  # noqa

from app.domains.user.models import User, UserRole
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension
from app.domains.gaming_booking.models import GamingBooking
from app.domains.post.models import Post
from app.domains.reel.models import Reel
from app.domains.messaging.models import Conversation, ConversationParticipant, Message
from app.domains.friend.models import Friendship
from app.domains.follow.models import Follow

DEMO_PASS = "Demo@123"
HASHED_PASS = hash_password(DEMO_PASS)

DEMO_USERS = [
    {"full_name": "Manish Kumar", "username": "lens_by_manish", "phone": "+919999999010", "email": "manish@paythan.dev", "city": "Delhi", "lat": 28.6139, "lng": 77.2090},
    {"full_name": "Ananya Sharma", "username": "ananya_gamer", "phone": "+919999999011", "email": "ananya@paythan.dev", "city": "Delhi", "lat": 28.6210, "lng": 77.2150},
    {"full_name": "Rohan Verma", "username": "rohan_playz", "phone": "+919999999012", "email": "rohan@paythan.dev", "city": "Gurgaon", "lat": 28.4595, "lng": 77.0266},
    {"full_name": "Priya Malhotra", "username": "priya_arcade", "phone": "+919999999013", "email": "priya@paythan.dev", "city": "Delhi", "lat": 28.5670, "lng": 77.2100},
    {"full_name": "Test User", "username": "test_user", "phone": "+919999999014", "email": "test@paythan.dev", "city": "Noida", "lat": 28.5700, "lng": 77.3200},
    {"full_name": "Amit Singh", "username": "amit_esports", "phone": "+919999999015", "email": "amit@paythan.dev", "city": "Delhi", "lat": 28.6400, "lng": 77.2200},
]

def make_id() -> uuid.UUID:
    return uuid.uuid4()

async def seed(session: AsyncSession) -> None:
    print("=== Seeding Paythan Demo Data ===")

    # Clear previous demo data to avoid uniques
    await session.execute(text("DELETE FROM gaming_bookings WHERE booking_ref LIKE 'PB1%'"))
    await session.execute(text("DELETE FROM posts WHERE content LIKE '%BGMI%' OR content LIKE '%PS5%'"))
    await session.execute(text("DELETE FROM reels WHERE caption LIKE '%Demo Reel%'"))
    await session.execute(text("DELETE FROM conversations"))  # cascade messages
    # users keep if re-run

    # 1. Users
    user_map = {}
    for ud in DEMO_USERS:
        existing = await session.execute(select(User).where(User.phone == ud["phone"]))
        u = existing.scalar_one_or_none()
        if not u:
            u = User(
                id=make_id(),
                full_name=ud["full_name"],
                username=ud["username"],
                email=ud["email"],
                phone=ud["phone"],
                hashed_password=HASHED_PASS,
                avatar_url=f"https://picsum.photos/id/{10 + hash(ud['phone']) % 50}/200/200",
                role=UserRole.USER,
                is_active=True,
                is_verified=True,
                phone_verified=True,
                email_verified=True,
                city=ud["city"],
                latitude=ud["lat"],
                longitude=ud["lng"],
                location_updated_at=datetime.now(timezone.utc),
            )
            session.add(u)
            await session.flush()
        user_map[ud["username"]] = u
        print(f"User: {ud['username']} / {ud['phone']} (pw: {DEMO_PASS})")

    main_user = user_map["lens_by_manish"]
    await session.commit()

    # 2. Gaming Place Extensions (for demo parlors from existing places)
    places = (await session.execute(select(GamingPlace).limit(6))).scalars().all()
    if not places:
        print("No gaming_places found — abort")
        return

    for idx, place in enumerate(places[:6]):
        owner = list(user_map.values())[idx % len(user_map)]
        ext = await session.get(GamingPlaceExtension, place.id)
        if not ext:
            ext = GamingPlaceExtension(gaming_place_id=place.id)
            session.add(ext)
        ext.owner_id = owner.id
        ext.is_verified = True
        ext.price_per_hour = Decimal("149")
        ext.original_price = Decimal("599")
        ext.discount_percent = Decimal("75")
        ext.follower_count = 120 + idx * 30
        ext.post_count = 3 + idx
        ext.is_wizard_enabled = True
        ext.is_couples_allowed = idx % 2 == 0
        print(f"Extension for {place.name} owned by {owner.username}")

    await session.commit()

    # 3. Bookings (mix statuses)
    booking_statuses = ["confirmed", "completed", "cancelled", "confirmed", "completed", "confirmed"]
    for i, status in enumerate(booking_statuses):
        place = places[i % len(places)]
        user = list(user_map.values())[i % len(user_map)]
        today = date.today()
        bdate = today + timedelta(days= (i-2) )
        b = GamingBooking(
            id=make_id(),
            booking_ref=f"PB{1000+i}",
            user_id=user.id,
            parlour_id=place.id,
            guest_name=user.full_name,
            num_players=2 + (i % 3),
            slot_date=bdate,
            start_time=time(18 + (i%3), 0),
            end_time=time(20 + (i%3), 0),
            hours_booked=Decimal("2"),
            price_per_hour=Decimal("149"),
            total_price=Decimal("298"),
            final_price=Decimal("298"),
            payment_mode="pay_at_parlor",
            payment_status="pending" if status != "completed" else "paid",
            booking_status=status,
            created_at=datetime.now(timezone.utc) - timedelta(days=abs(i-2)),
        )
        session.add(b)
    print(f"Added {len(booking_statuses)} demo bookings")

    await session.commit()

    # 4. Posts (social feed)
    post_contents = [
        "BGMI squad night at Neon Arena! Who is in?",
        "New PS5 controllers just arrived 🔥 Book your slot",
        "Valorant 5v5 tournament this weekend - prizes worth 10k",
        "Chill gaming with friends at Pixel Pit. Epic vibes!",
        "First time trying VR at Apex Room - mind blown!",
        "League night every Friday. Free entry for members.",
    ]
    for i, content in enumerate(post_contents):
        place = places[i % len(places)]
        p = Post(
            id=make_id(),
            parlor_id=place.id,
            content=content,
            media_urls=[f"https://picsum.photos/id/{200 + i}/800/600"],
            likes_count=12 + i*5,
            comments_count=3 + i,
            created_at=datetime.now(timezone.utc) - timedelta(hours=i*4),
        )
        session.add(p)
    print("Added 6 demo posts")

    await session.commit()

    # 5. Reels (5s demo)
    reel_captions = [
        "Insane headshot streak at Neon! #BGMI",
        "New setup reveal - RGB everything",
        "5s of pure gaming chaos 😂",
        "Victory royale in 5 seconds flat",
        "Late night grind at the parlor",
    ]
    # Use public playable videos (short clips)
    public_videos = [
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
    ]
    for i, cap in enumerate(reel_captions):
        user = list(user_map.values())[i % len(user_map)]
        r = Reel(
            id=make_id(),
            user_id=user.id,
            video_url=public_videos[i],
            thumbnail_url=f"https://picsum.photos/id/{30 + i}/360/640",
            caption=cap,
            duration_seconds=5,
            width=640,
            height=360,
            aspect_ratio="9:16",
            likes_count=45 + i*10,
            views_count=300 + i*50,
            created_at=datetime.now(timezone.utc) - timedelta(hours=2+i),
        )
        session.add(r)
    print("Added 5 demo reels (playable public clips)")

    await session.commit()

    # 6. Messaging demo
    # Simple convos + messages
    conv_users = list(user_map.values())[:4]
    for i in range(3):
        u1 = conv_users[i]
        u2 = conv_users[(i+1) % len(conv_users)]
        # find or create direct
        existing = await session.execute(
            text("SELECT c.id FROM conversations c JOIN conversation_participants cp1 ON cp1.conversation_id=c.id AND cp1.user_id=:u1 JOIN conversation_participants cp2 ON cp2.conversation_id=c.id AND cp2.user_id=:u2 LIMIT 1"),
            {"u1": str(u1.id), "u2": str(u2.id)}
        )
        row = existing.first()
        if row:
            cid = uuid.UUID(row[0])
        else:
            c = Conversation(id=make_id(), type="direct")
            session.add(c)
            await session.flush()
            session.add_all([
                ConversationParticipant(conversation_id=c.id, user_id=u1.id),
                ConversationParticipant(conversation_id=c.id, user_id=u2.id),
            ])
            cid = c.id

        # messages
        msgs = [
            f"Hey, booking for tonight?",
            "Yes! See you at the parlor 🔥",
        ]
        for j, m in enumerate(msgs):
            sender = u1 if j == 0 else u2
            msg = Message(
                id=make_id(),
                conversation_id=cid,
                sender_id=sender.id,
                content=m,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30-j*10),
            )
            session.add(msg)

    print("Added demo conversations + messages")

    # 7. Some follows / friends for social
    for i, u in enumerate(list(user_map.values())[:5]):
        other = list(user_map.values())[(i+1) % 5]
        # friend
        await session.execute(text("INSERT OR IGNORE INTO friendships (id, user1_id, user2_id, created_at) VALUES (:id, :u1, :u2, :ts)"),
            {"id": str(make_id()), "u1": str(u.id), "u2": str(other.id), "ts": datetime.now(timezone.utc).isoformat()})
        # follow parlor
        if places:
            await session.execute(text("INSERT OR IGNORE INTO follows (id, user_id, parlor_id, created_at) VALUES (:id, :uid, :pid, :ts)"),
                {"id": str(make_id()), "uid": str(u.id), "pid": str(places[i % len(places)].id), "ts": datetime.now(timezone.utc).isoformat()})

    await session.commit()

    print("\n=== DEMO DATA SEEDED SUCCESSFULLY ===")
    print("Login examples:")
    for ud in DEMO_USERS[:3]:
        print(f"  Phone: {ud['phone']}  Password: {DEMO_PASS}")
    print("\nRun backend + flutter app. All major flows should have data.")

async def main() -> None:
    db_session.get_settings.cache_clear() if hasattr(db_session, "get_settings") else None
    db_session._engine = None
    db_session._session_factory = None

    engine = db_session.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = db_session.get_session_factory()
    async with factory() as session:
        # optional: clear demo-ish data (comment to preserve)
        # await session.execute(text("DELETE FROM users WHERE phone LIKE '+91999999901%'"))
        await seed(session)

if __name__ == "__main__":
    asyncio.run(main())
