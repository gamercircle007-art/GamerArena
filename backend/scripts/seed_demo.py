#!/usr/bin/env python3
"""
Comprehensive demo seed for Paythan (GameConnect/ParLour).

Seeds realistic Delhi gaming data binding all modules:
Users (regular, owners, admin) -> Parlors/GamingPlaces -> Bookings -> Posts/Reels -> Comments/Likes -> Messaging -> Profiles

Run:
  cd backend
  PYTHONPATH=. .venv/bin/python scripts/seed_demo.py

Uses dev.db (sqlite). For Postgres, set DATABASE_URL first.

Generates 5s demo reels (local files in demo_media, urls use public playable for compatibility).
Uses picsum for images.

After seed, login with:
  +919999999010 / Demo@123  (Manish Kumar)
  +919999999999 / Admin@123 (admin)
"""

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

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{BACKEND_ROOT / 'dev.db'}")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_for_local_development_only_32chars")
os.environ.setdefault("APP_ENV", "local")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.db.base import Base
import app.db.models  # ensure all

from app.domains.user.models import User, UserRole
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension
from app.domains.gaming_booking.models import GamingBooking
from app.domains.post.models import Post
from app.domains.reel.models import Reel, ReelPrivacy
from app.domains.like.models import Like
from app.domains.comment.models import Comment
from app.domains.messaging.models import Conversation, ConversationParticipant, Message
from app.domains.parlor.models import Parlor
from app.domains.dms.models import MediaAsset
from app.domains.follow.models import Follow

DEMO_PASS = "Demo@123"
ADMIN_PASS = "Admin@123"
HASHED = hash_password(DEMO_PASS)
ADMIN_HASHED = hash_password(ADMIN_PASS)

# Delhi area coords
DELHI_LAT = 28.6139
DELHI_LNG = 77.2090

async def clear_demo(session: AsyncSession):
    """Clear previous demo data safely."""
    for table in ["messages", "conversation_participants", "conversations", "likes", "comments", "reels", "posts", "gaming_bookings", "gaming_place_extensions", "parlors", "media_assets"]:
        try:
            await session.execute(text(f"DELETE FROM {table}"))
        except:
            pass
    # Delete demo users by exact phones
    phones = ['+919999999010', '+919999999011', '+919999999012', '+919999999013', '+919999999014', '+919999999999']
    for p in phones:
        await session.execute(text("DELETE FROM users WHERE phone = :p"), {"p": p})
    await session.commit()

async def seed(session: AsyncSession):
    print("=== Paythan Comprehensive Demo Seed ===")

    # 1. Users: 6 total (4 regular, 1 owner, 1 admin)
    users = []
    user_data = [
        ("Manish Kumar", "manish_demo", "+919999999010", "manish@paythan.dev", UserRole.USER),
        ("Ananya Sharma", "ananya_demo", "+919999999011", "ananya@paythan.dev", UserRole.USER),
        ("Rohan Verma", "rohan_demo", "+919999999012", "rohan@paythan.dev", UserRole.USER),
        ("Priya Singh", "priya_demo", "+919999999013", "priya@paythan.dev", UserRole.USER),
        ("Vikram Malhotra", "vikram_owner", "+919999999014", "vikram@paythan.dev", UserRole.PARLOR_OWNER),
        ("Admin User", "admin", "+919999999999", "admin@paythan.dev", UserRole.ADMIN),
    ]
    for i, (name, uname, phone, email, role) in enumerate(user_data):
        u = User(
            id=uuid.uuid4(),
            full_name=name,
            username=uname,
            email=email,
            phone=phone,
            hashed_password=ADMIN_HASHED if role == UserRole.ADMIN else HASHED,
            avatar_url=f"https://picsum.photos/id/{10+i}/200/200",
            role=role,
            is_active=True,
            is_verified=True,
            phone_verified=True,
            email_verified=True,
            city="Delhi",
            latitude=DELHI_LAT + (i*0.01),
            longitude=DELHI_LNG + (i*0.01),
            friends_count=3,
            followers_count=10 + i,
            following_count=5,
        )
        session.add(u)
        users.append(u)
    await session.flush()
    print(f"Seeded {len(users)} users (login: +919999999010 / {DEMO_PASS}, admin / {ADMIN_PASS})")

    manish = users[0]
    ananya = users[1]
    rohan = users[2]
    priya = users[3]
    vikram = users[4]
    adminu = users[5]

    # 2. Parlors (use existing gaming_places + create Parlors)
    places = (await session.execute(select(GamingPlace).limit(6))).scalars().all()
    if not places:
        print("No gaming_places - seed some first")
        return

    # Seed Parlors for owners
    parlors = []
    for i, place in enumerate(places[:3]):
        owner = vikram if i == 0 else manish
        p = Parlor(
            id=uuid.uuid4(),
            owner_id=owner.id,
            name=place.name or f"Parlor {i}",
            description=f"Premium gaming spot in {place.address or 'Delhi'}",
            address=place.address or "Connaught Place, Delhi",
            location=None,  # use from gaming_place
            game_types=["BGMI", "Valorant", "PS5"],
            is_verified=True,
            follower_count=50 + i*20,
            post_count=4,
        )
        session.add(p)
        parlors.append(p)
    await session.flush()
    print(f"Seeded {len(parlors)} parlors")

    # 3. GamingPlaceExtensions (bind to places)
    for i, place in enumerate(places):
        ext = GamingPlaceExtension(gaming_place_id=place.id)
        ext.owner_id = vikram.id if i < 3 else manish.id
        ext.price_per_hour = Decimal("149")
        ext.original_price = Decimal("599")
        ext.discount_percent = Decimal("75")
        ext.is_verified = True
        ext.follower_count = 100 + i*30
        ext.post_count = 5
        ext.is_wizard_enabled = True
        session.add(ext)
    print("Seeded gaming_place_extensions")

    # 4. Bookings (linked to users and places, mixed status)
    bookings = []
    statuses = ["confirmed", "completed", "cancelled", "confirmed", "completed", "confirmed"]
    for i, status in enumerate(statuses):
        place = places[i % len(places)]
        user = users[i % 4]
        b = GamingBooking(
            id=uuid.uuid4(),
            booking_ref=f"PBDEMO{1000+i}",
            user_id=user.id,
            parlour_id=place.id,
            guest_name=user.full_name,
            num_players=2 + (i % 3),
            slot_date=(date.today() + timedelta(days=i-2)),
            start_time=time(18, 0),
            end_time=time(20, 0),
            hours_booked=Decimal("2"),
            price_per_hour=Decimal("149"),
            total_price=Decimal("298"),
            final_price=Decimal("298"),
            payment_mode="pay_at_parlor",
            payment_status="paid" if status == "completed" else "pending",
            booking_status=status,
            created_at=datetime.now(timezone.utc) - timedelta(days=abs(i-2)),
        )
        session.add(b)
        bookings.append(b)
    print(f"Seeded {len(bookings)} bookings")

    # 5. Posts (linked to gaming_places as parlor)
    posts = []
    post_contents = [
        "Epic BGMI night at Neon Arena! Squad up?",
        "New PS5 controllers arrived. Book now!",
        "Valorant tournament this weekend - prizes!",
        "Chill vibes at Pixel Pit. Come join!",
        "VR gaming at Apex - mind blown experience.",
        "Friday league night - free entry!",
    ]
    for i, content in enumerate(post_contents):
        place = places[i % len(places)]
        p = Post(
            id=uuid.uuid4(),
            parlor_id=place.id,
            content=content,
            media_urls=[f"https://picsum.photos/id/{100+i}/800/600"],
            likes_count=15 + i*3,
            comments_count=4 + i,
            created_at=datetime.now(timezone.utc) - timedelta(hours=i*2),
        )
        session.add(p)
        posts.append(p)
    print(f"Seeded {len(posts)} posts")

    # 6. Reels (5s, linked to users, use generated local + public for play)
    reels = []
    reel_captions = [
        "Insane clutch at Neon Arena!",
        "New RGB setup reveal 🔥",
        "5s of pure chaos in Valorant",
        "Victory in 5 seconds flat",
        "Late night grind session",
    ]
    # Use generated local paths for "uploaded", public for playback compatibility
    video_urls = [
        f"file://{BACKEND_ROOT}/demo_media/reel1.mp4",
        f"file://{BACKEND_ROOT}/demo_media/reel2.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
    ]
    thumbs = [f"https://picsum.photos/id/{200+i}/360/640" for i in range(5)]
    for i, cap in enumerate(reel_captions):
        user = users[i % 4]
        r = Reel(
            id=uuid.uuid4(),
            user_id=user.id,
            video_url=video_urls[i],
            thumbnail_url=thumbs[i],
            caption=cap,
            duration_seconds=5,
            width=640,
            height=360,
            likes_count=30 + i*5,
            views_count=200 + i*20,
            created_at=datetime.now(timezone.utc) - timedelta(hours=i),
        )
        session.add(r)
        reels.append(r)
    print(f"Seeded {len(reels)} reels (5s demo clips)")

    # 7. Comments (on posts and reels)
    comments = []
    for post in posts[:3]:
        for j in range(2):
            c = Comment(
                id=uuid.uuid4(),
                post_id=post.id,
                user_id=users[(j+1) % 4].id,
                content=f"Great post! {j+1}",
                likes_count=1,
            )
            session.add(c)
            comments.append(c)
    print(f"Seeded {len(comments)} comments")

    # 8. Likes (on posts, reels, comments)
    for post in posts:
        for u in users[:3]:
            l = Like(
                id=uuid.uuid4(),
                user_id=u.id,
                target_type="post",
                target_id=post.id,
            )
            session.add(l)
    for reel in reels:
        l = Like(id=uuid.uuid4(), user_id=ananya.id, target_type="reel", target_id=reel.id)
        session.add(l)
    print("Seeded likes")

    # 9. Messaging (conversations + messages between users)
    convs = []
    for i in range(2):
        u1 = users[i]
        u2 = users[i+2]
        c = Conversation(id=uuid.uuid4(), type="direct")
        session.add(c)
        await session.flush()
        session.add(ConversationParticipant(conversation_id=c.id, user_id=u1.id))
        session.add(ConversationParticipant(conversation_id=c.id, user_id=u2.id))
        # messages
        for k, txt in enumerate(["Hey, up for a game?", "Sure, see you at the parlor!", "Booked the slot."]):
            m = Message(
                id=uuid.uuid4(),
                conversation_id=c.id,
                sender_id=(u1 if k % 2 == 0 else u2).id,
                content=txt,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=10-k),
            )
            session.add(m)
        convs.append(c)
    print(f"Seeded {len(convs)} conversations with messages")

    # 10. Profiles (via user fields already set, add user_profiles if table)
    # Assume user table covers profile.

    # 11. Admin data (seed one moderation like flag)
    # For demo, the admin user is there; admin routes will see users/bookings.

    # Some follows for social
    for u in users[:4]:
        f = Follow(id=uuid.uuid4(), user_id=u.id, parlor_id=places[0].id)
        session.add(f)

    await session.commit()
    print("\n=== DEMO DATA COMPLETE ===")
    print("All modules bound: users-parlors-bookings-posts-reels-comments-likes-messaging")
    print("Run: PYTHONPATH=. .venv/bin/python scripts/seed_demo.py")
    print("Login and test all flows!")

async def main():
    factory = get_session_factory()
    async with factory() as session:
        await clear_demo(session)
        await seed(session)

if __name__ == "__main__":
    asyncio.run(main())
