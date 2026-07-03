"""Friend system business logic."""

from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.common.social_notify import notify_user
from app.domains.friend.models import FriendRequest, Friendship, UserBlock
from app.domains.friend.schemas import (
    FriendRequestResponse,
    FriendSuggestion,
    FriendshipResponse,
    MutualFriendsResponse,
    UserSummary,
)
from app.domains.user.models import User
from app.domains.user.repository import UserRepository
from app.ws.events import publish_to_user


def _canonical_pair(a: UUID, b: UUID) -> tuple[UUID, UUID]:
    return (a, b) if str(a) < str(b) else (b, a)


class FriendService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def is_blocked(self, user1: UUID, user2: UUID) -> bool:
        result = await self.session.execute(
            select(UserBlock).where(
                or_(
                    and_(UserBlock.blocker_id == user1, UserBlock.blocked_id == user2),
                    and_(UserBlock.blocker_id == user2, UserBlock.blocked_id == user1),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def are_friends(self, user1: UUID, user2: UUID) -> bool:
        u1, u2 = _canonical_pair(user1, user2)
        result = await self.session.execute(
            select(Friendship).where(Friendship.user1_id == u1, Friendship.user2_id == u2)
        )
        return result.scalar_one_or_none() is not None

    async def _friend_ids(self, user_id: UUID) -> list[UUID]:
        result = await self.session.execute(
            select(Friendship).where(
                or_(Friendship.user1_id == user_id, Friendship.user2_id == user_id)
            )
        )
        ids: list[UUID] = []
        for f in result.scalars().all():
            ids.append(f.user2_id if f.user1_id == user_id else f.user1_id)
        return ids

    async def send_friend_request(
        self, sender_id: UUID, receiver_id: UUID, redis: aioredis.Redis
    ) -> dict:
        if sender_id == receiver_id:
            raise ValidationError("Cannot add yourself")
        if await self.is_blocked(sender_id, receiver_id):
            raise ValidationError("Cannot send request to this user")
        if await self.are_friends(sender_id, receiver_id):
            raise ValidationError("Already friends")

        existing = await self.session.execute(
            select(FriendRequest).where(
                FriendRequest.sender_id == sender_id,
                FriendRequest.receiver_id == receiver_id,
                FriendRequest.status == "pending",
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationError("Request already sent")

        reverse = await self.session.execute(
            select(FriendRequest).where(
                FriendRequest.sender_id == receiver_id,
                FriendRequest.receiver_id == sender_id,
                FriendRequest.status == "pending",
            )
        )
        reverse_req = reverse.scalar_one_or_none()
        if reverse_req:
            return await self.accept_friend_request(reverse_req.id, receiver_id, redis)

        req = FriendRequest(sender_id=sender_id, receiver_id=receiver_id, status="pending")
        self.session.add(req)
        await self.session.commit()
        await self.session.refresh(req)

        sender = await self.user_repo.get_by_id(sender_id)
        await publish_to_user(
            redis,
            receiver_id,
            {
                "type": "friend_request",
                "request": {
                    "id": str(req.id),
                    "sender": {
                        "id": str(sender_id),
                        "name": sender.full_name if sender else None,
                        "avatar_url": sender.avatar_url if sender else None,
                        "username": sender.username if sender else None,
                    },
                    "created_at": req.created_at.isoformat(),
                },
            },
        )
        await notify_user(
            self.session,
            redis,
            receiver_id,
            type="friend_request",
            title="Friend request",
            body=f"{sender.full_name if sender else 'Someone'} sent you a friend request",
            data={"request_id": str(req.id), "sender_id": str(sender_id)},
            skip_if_online=True,
        )
        return {"id": str(req.id), "status": "pending"}

    async def accept_friend_request(
        self, request_id: UUID, accepting_user_id: UUID, redis: aioredis.Redis
    ) -> dict:
        req = await self.session.get(FriendRequest, request_id)
        if req is None or req.receiver_id != accepting_user_id:
            raise NotFoundError("Request not found")
        if req.status != "pending":
            raise ValidationError(f"Request is already {req.status}")

        req.status = "accepted"
        req.responded_at = datetime.now(timezone.utc)
        u1, u2 = _canonical_pair(req.sender_id, req.receiver_id)
        friendship = Friendship(user1_id=u1, user2_id=u2)
        self.session.add(friendship)
        await self.session.execute(
            update(User).where(User.id == req.sender_id).values(friends_count=User.friends_count + 1)
        )
        await self.session.execute(
            update(User).where(User.id == req.receiver_id).values(friends_count=User.friends_count + 1)
        )
        await self.session.commit()

        accepting_user = await self.user_repo.get_by_id(accepting_user_id)
        await publish_to_user(
            redis,
            req.sender_id,
            {
                "type": "friend_accepted",
                "friend": {
                    "id": str(accepting_user_id),
                    "name": accepting_user.full_name if accepting_user else None,
                    "avatar_url": accepting_user.avatar_url if accepting_user else None,
                },
            },
        )
        await notify_user(
            self.session,
            redis,
            req.sender_id,
            type="friend_accepted",
            title="Friend request accepted",
            body=f"{accepting_user.full_name if accepting_user else 'Someone'} accepted your friend request",
            data={"friend_id": str(accepting_user_id)},
            skip_if_online=True,
        )
        return {"status": "accepted", "friendship_id": str(friendship.id)}

    async def decline_friend_request(self, request_id: UUID, user_id: UUID) -> dict:
        req = await self.session.get(FriendRequest, request_id)
        if req is None or req.receiver_id != user_id:
            raise NotFoundError("Request not found")
        req.status = "declined"
        req.responded_at = datetime.now(timezone.utc)
        await self.session.commit()
        return {"status": "declined"}

    async def cancel_friend_request(self, request_id: UUID, user_id: UUID) -> None:
        req = await self.session.get(FriendRequest, request_id)
        if req is None or req.sender_id != user_id:
            raise NotFoundError("Request not found")
        await self.session.delete(req)
        await self.session.commit()

    async def list_incoming_requests(self, user_id: UUID) -> list[FriendRequestResponse]:
        result = await self.session.execute(
            select(FriendRequest, User)
            .join(User, User.id == FriendRequest.sender_id)
            .where(FriendRequest.receiver_id == user_id, FriendRequest.status == "pending")
            .order_by(FriendRequest.created_at.desc())
        )
        return [
            FriendRequestResponse(
                id=req.id,
                sender=UserSummary.model_validate(user),
                created_at=req.created_at,
            )
            for req, user in result.all()
        ]

    async def list_sent_requests(self, user_id: UUID) -> list[FriendRequestResponse]:
        result = await self.session.execute(
            select(FriendRequest, User)
            .join(User, User.id == FriendRequest.receiver_id)
            .where(FriendRequest.sender_id == user_id, FriendRequest.status == "pending")
            .order_by(FriendRequest.created_at.desc())
        )
        return [
            FriendRequestResponse(
                id=req.id,
                sender=UserSummary.model_validate(user),
                created_at=req.created_at,
            )
            for req, user in result.all()
        ]

    async def list_friends(self, user_id: UUID) -> list[FriendshipResponse]:
        result = await self.session.execute(
            select(Friendship).where(
                or_(Friendship.user1_id == user_id, Friendship.user2_id == user_id)
            )
        )
        responses: list[FriendshipResponse] = []
        for f in result.scalars().all():
            friend_id = f.user2_id if f.user1_id == user_id else f.user1_id
            user = await self.user_repo.get_by_id(friend_id)
            if user:
                responses.append(
                    FriendshipResponse(
                        id=f.id,
                        user=UserSummary.model_validate(user),
                        created_at=f.created_at,
                    )
                )
        return responses

    async def unfriend(self, user_id: UUID, friend_id: UUID) -> None:
        u1, u2 = _canonical_pair(user_id, friend_id)
        result = await self.session.execute(
            select(Friendship).where(Friendship.user1_id == u1, Friendship.user2_id == u2)
        )
        friendship = result.scalar_one_or_none()
        if friendship is None:
            raise NotFoundError("Friendship not found")
        await self.session.delete(friendship)
        await self.session.execute(
            update(User).where(User.id == user_id).values(friends_count=func.greatest(User.friends_count - 1, 0))
        )
        await self.session.execute(
            update(User).where(User.id == friend_id).values(friends_count=func.greatest(User.friends_count - 1, 0))
        )
        await self.session.commit()

    async def block_user(self, blocker_id: UUID, blocked_id: UUID) -> None:
        if blocker_id == blocked_id:
            raise ValidationError("Cannot block yourself")
        if await self.are_friends(blocker_id, blocked_id):
            await self.unfriend(blocker_id, blocked_id)
        existing = await self.session.execute(
            select(UserBlock).where(
                UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id
            )
        )
        if existing.scalar_one_or_none() is None:
            self.session.add(UserBlock(blocker_id=blocker_id, blocked_id=blocked_id))
            await self.session.commit()

    async def unblock_user(self, blocker_id: UUID, blocked_id: UUID) -> None:
        result = await self.session.execute(
            select(UserBlock).where(
                UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id
            )
        )
        block = result.scalar_one_or_none()
        if block:
            await self.session.delete(block)
            await self.session.commit()

    async def list_blocked(self, user_id: UUID) -> list[UserSummary]:
        result = await self.session.execute(
            select(User)
            .join(UserBlock, UserBlock.blocked_id == User.id)
            .where(UserBlock.blocker_id == user_id)
        )
        return [UserSummary.model_validate(u) for u in result.scalars().all()]

    async def get_mutual_friends(self, user1: UUID, user2: UUID) -> MutualFriendsResponse:
        friends1 = set(await self._friend_ids(user1))
        friends2 = set(await self._friend_ids(user2))
        mutual_ids = friends1 & friends2
        friends: list[UserSummary] = []
        for fid in list(mutual_ids)[:20]:
            user = await self.user_repo.get_by_id(fid)
            if user:
                friends.append(UserSummary.model_validate(user))
        return MutualFriendsResponse(count=len(mutual_ids), friends=friends)

    async def get_suggestions(self, user_id: UUID, limit: int = 20) -> list[FriendSuggestion]:
        my_friends = await self._friend_ids(user_id)
        if not my_friends:
            result = await self.session.execute(
                select(User).where(User.id != user_id).limit(limit)
            )
            return [
                FriendSuggestion(user=UserSummary.model_validate(u), mutual_friends=0)
                for u in result.scalars().all()
            ]

        result = await self.session.execute(
            select(User, func.count().label("mutual"))
            .join(
                Friendship,
                or_(Friendship.user1_id == User.id, Friendship.user2_id == User.id),
            )
            .where(
                User.id != user_id,
                User.id.notin_(my_friends),
                or_(
                    and_(Friendship.user1_id.in_(my_friends), Friendship.user2_id == User.id),
                    and_(Friendship.user2_id.in_(my_friends), Friendship.user1_id == User.id),
                ),
            )
            .group_by(User.id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [
            FriendSuggestion(user=UserSummary.model_validate(row[0]), mutual_friends=int(row[1]))
            for row in result.all()
        ]