#!/usr/bin/env python3
"""
Seed demo users, friend requests, friendships, follows, and messaging data
for testing the new DM / messaging UI.

Usage:
  cd backend
  PYTHONPATH=. .venv/bin/python scripts/seed_messaging_demo.py

Login credentials for all demo users:
  Password: Demo@123
  (Use phone + password login, or OTP bypass in dev if enabled)

Creates ~5 regular users + relations so inbox + new message + chats are populated.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
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
import app.db.models  # noqa: F401  (ensure all models registered)

from app.domains.user.models import User, UserRole
from app.domains.friend.models import FriendRequest, Friendship
from app.domains.messaging.models import Conversation, ConversationParticipant, Message
from app.domains.reel.models import UserFollow  # user <-> user follows

# Demo password for all test users (easy to remember)
DEMO_PASSWORD = "Demo@123"
HASHED = hash_password(DEMO_PASSWORD)

# Users inspired by screenshots + gaming theme
DEMO_USERS = [
    {
        "full_name": "Manish Lens",
        "username": "lens_by_manish",
        "email": "manish@gameconnect.dev",
        "phone": "+919999999010",
        "avatar_url": "https://picsum.photos/id/1008/200/200",
    },
    {
        "full_name": "Sheera Khan",
        "username": "heyitssheera",
        "email": "sheera@gameconnect.dev",
        "phone": "+919999999011",
        "avatar_url": "https://picsum.photos/id/1009/200/200",
    },
    {
        "full_name": "Tanuj Agrawal",
        "username": "tnu.agrwl",
        "email": "tanuj@gameconnect.dev",
        "phone": "+919999999012",
        "avatar_url": "https://picsum.photos/id/1011/200/200",
    },
    {
        "full_name": "Sheera Fitness",
        "username": "fitnes_with_joy",
        "email": "sheerafit@gameconnect.dev",
        "phone": "+919999999013",
        "avatar_url": "https://picsum.photos/id/1012/200/200",
    },
    {
        "full_name": "Manish Lightweaver",
        "username": "lightweaver",
        "email": "lightweaver@gameconnect.dev",
        "phone": "+919999999014",
        "avatar_url": "https://picsum.photos/id/160/200/200",
    },
    {
        "full_name": "Rimlina Hazarika",
        "username": "rimsplayz",
        "email": "rimlina@gameconnect.dev",
        "phone": "+919999999015",
        "avatar_url": "https://picsum.photos/id/64/200/200",
    },
]

async def get_or_create_user(session: AsyncSession, data: dict) -> User:
    result = await session.execute(
        select(User).where(User.phone == data["phone"])
    )
    user = result.scalar_one_or_none()
    if user:
        # update a few fields for demo
        user.full_name = data["full_name"]
        user.username = data["username"]
        user.avatar_url = data["avatar_url"]
        user.is_active = True
        user.is_verified = True
        user.phone_verified = True
        user.hashed_password = HASHED
        return user

    user = User(
        id=uuid.uuid4(),
        full_name=data["full_name"],
        username=data["username"],
        email=data["email"],
        phone=data["phone"],
        hashed_password=HASHED,
        avatar_url=data["avatar_url"],
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        phone_verified=True,
        email_verified=True,
    )
    session.add(user)
    return user

async def seed_demo_data() -> None:
    db_session.get_settings.cache_clear() if hasattr(db_session, "get_settings") else None
    db_session._engine = None
    db_session._session_factory = None

    engine = db_session.get_engine()
    # Ensure tables (safe if already there)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = db_session.get_session_factory()
    async with factory() as session:
        # 1. Create / update demo users
        created_users: dict[str, User] = {}
        for u_data in DEMO_USERS:
            u = await get_or_create_user(session, u_data)
            created_users[u.username] = u
            print(f"User ready: {u.username} / {u.phone} (pw: {DEMO_PASSWORD})")

        await session.commit()  # commit users first

        main_user = created_users["lens_by_manish"]
        sheera = created_users["heyitssheera"]
        tnu = created_users["tnu.agrwl"]
        fitjoy = created_users["fitnes_with_joy"]
        light = created_users["lightweaver"]
        rims = created_users["rimsplayz"]

        # 2. Friend requests (some pending for "Requests" testing)
        # Pending: sheera -> main, tnu -> main
        pending_pairs = [(sheera, main_user), (tnu, main_user)]
        for sender, receiver in pending_pairs:
            exists = await session.execute(
                select(FriendRequest).where(
                    FriendRequest.sender_id == sender.id,
                    FriendRequest.receiver_id == receiver.id,
                    FriendRequest.status == "pending",
                )
            )
            if not exists.scalar_one_or_none():
                req = FriendRequest(
                    id=uuid.uuid4(),
                    sender_id=sender.id,
                    receiver_id=receiver.id,
                    status="pending",
                )
                session.add(req)
                print(f"  FriendRequest pending: {sender.username} -> {receiver.username}")

        # Accepted requests -> friendships (main <-> fitjoy, main <-> light, sheera <-> tnu)
        accepted_pairs = [
            (main_user, fitjoy),
            (main_user, light),
            (sheera, tnu),
        ]
        for a, b in accepted_pairs:
            u1, u2 = (a.id, b.id) if str(a.id) < str(b.id) else (b.id, a.id)
            exists = await session.execute(
                select(Friendship).where(
                    Friendship.user1_id == u1, Friendship.user2_id == u2
                )
            )
            if not exists.scalar_one_or_none():
                fs = Friendship(id=uuid.uuid4(), user1_id=u1, user2_id=u2)
                session.add(fs)
                print(f"  Friendship: {a.username} <-> {b.username}")

        # Update friend counts (simple)
        for u in [main_user, sheera, tnu, fitjoy, light]:
            friend_count = await session.scalar(
                select(text("COUNT(*)")).select_from(
                    text("friendships")
                ).where(
                    text(f"user1_id = '{u.id}' OR user2_id = '{u.id}'")
                )
            )
            u.friends_count = friend_count or 0

        await session.commit()

        # 3. Some user <-> user follows (for social)
        follow_pairs = [(main_user, sheera), (light, main_user), (rims, fitjoy)]
        for follower, following in follow_pairs:
            exists = await session.execute(
                select(UserFollow).where(
                    UserFollow.follower_id == follower.id,
                    UserFollow.following_id == following.id,
                )
            )
            if not exists.scalar_one_or_none():
                uf = UserFollow(
                    id=uuid.uuid4(),
                    follower_id=follower.id,
                    following_id=following.id,
                )
                session.add(uf)
                print(f"  UserFollow: {follower.username} follows {following.username}")

        await session.commit()

        # 4. Messaging data - conversations + messages
        # Helper to create/get direct conv + participants + messages
        async def ensure_dm(user_a: User, user_b: User, messages_data: list[dict]):
            # find existing direct
            res = await session.execute(
                text("""
                    SELECT c.id FROM conversations c
                    JOIN conversation_participants cp1 ON cp1.conversation_id = c.id AND cp1.user_id = :a
                    JOIN conversation_participants cp2 ON cp2.conversation_id = c.id AND cp2.user_id = :b
                    WHERE c.type = 'direct'
                    LIMIT 1
                """),
                {"a": str(user_a.id), "b": str(user_b.id)},
            )
            row = res.first()
            if row:
                conv_id = uuid.UUID(row[0])
            else:
                conv = Conversation(
                    id=uuid.uuid4(),
                    type="direct",
                    last_message_at=datetime.now(timezone.utc),
                )
                session.add(conv)
                await session.flush()

                session.add_all([
                    ConversationParticipant(conversation_id=conv.id, user_id=user_a.id),
                    ConversationParticipant(conversation_id=conv.id, user_id=user_b.id),
                ])
                conv_id = conv.id
                print(f"  Conversation created: {user_a.username} <-> {user_b.username}")

            # add messages
            for i, m in enumerate(messages_data):
                sender = user_a if m.get("from_a", True) else user_b
                msg = Message(
                    id=uuid.uuid4(),
                    conversation_id=conv_id,
                    sender_id=sender.id,
                    content=m["content"],
                    message_type="text",
                    is_ephemeral=False,
                    created_at=datetime.now(timezone.utc) - timedelta(minutes=30 * (len(messages_data) - i)),
                )
                session.add(msg)

            # last_message_at is set on creation; preview is derived in repo/service from messages
            last_ts = datetime.now(timezone.utc)
            await session.execute(
                text("UPDATE conversations SET last_message_at = :ts WHERE id = :id"),
                {"ts": last_ts.isoformat(), "id": str(conv_id)},
            )

        # Seed several convos for lens_by_manish
        await ensure_dm(
            main_user, sheera,
            [
                {"from_a": False, "content": "Hey! Did you see the new controllers at Neon Arena?"},
                {"from_a": True, "content": "Yeah! We should book a slot this weekend 🔥"},
                {"from_a": False, "content": "Sent a reel by heyitssheera"},
            ],
        )

        await ensure_dm(
            main_user, tnu,
            [
                {"from_a": True, "content": "Booking for Valorant 5v5 tonight?"},
                {"from_a": False, "content": "I'm in. 8pm?"},
            ],
        )

        await ensure_dm(
            main_user, fitjoy,
            [
                {"from_a": False, "content": "Loved your last reel! What game was that?"},
                {"from_a": True, "content": "BGMI at Pixel Pit. You should join next time."},
                {"from_a": False, "content": "Count me in!"},
                {"from_a": True, "content": "Perfect, I'll send the booking link."},
            ],
        )

        await ensure_dm(
            sheera, light,
            [
                {"from_a": True, "content": "We hitting LevelUp Lounge tomorrow?"},
            ],
        )

        await ensure_dm(
            main_user, rims,
            [
                {"from_a": False, "content": "Your story was fire 😂"},
                {"from_a": True, "content": "Haha thanks! New setup at the parlor."},
            ],
        )

        await session.commit()
        print("\n=== DEMO MESSAGING DATA SEEDED SUCCESSFULLY ===")
        print("Main test user: lens_by_manish / +919999999010 / Demo@123")
        print("Other users: heyitssheera, tnu.agrwl, fitnes_with_joy, lightweaver, rimsplayz")
        print("Open the app, login as one of them, go to Messages tab.")
        print("You should see chats in inbox + be able to start new from suggested (or friends).")

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
