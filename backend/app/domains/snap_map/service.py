"""Snap map and profile business logic."""

import json
import math
from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError
from app.domains.friend.service import FriendService
from app.domains.online.service import OnlineStatusService
from app.domains.snap_map.models import UserLocation, UserProfile
from app.domains.snap_map.schemas import (
    GhostModeUpdate,
    LocationPrivacyUpdate,
    LocationUpdate,
    ProfileUpdate,
    PublicProfileResponse,
    SnapMapUser,
)
from app.domains.user.models import User
from app.domains.user.repository import UserRepository
from app.ws.events import publish_to_user

LOCATION_KEY = "location:{}"
LOCATION_TTL = 600


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class SnapMapService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.friend_service = FriendService(session)

    async def _get_or_create_profile(self, user_id: UUID) -> UserProfile:
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self.session.add(profile)
            await self.session.flush()
        return profile

    async def update_location(
        self, user_id: UUID, data: LocationUpdate, redis: aioredis.Redis
    ) -> None:
        lat = round(data.lat, 3)
        lng = round(data.lng, 3)
        result = await self.session.execute(
            select(UserLocation).where(UserLocation.user_id == user_id)
        )
        loc = result.scalar_one_or_none()
        if loc:
            loc.latitude = lat
            loc.longitude = lng
            loc.accuracy = data.accuracy
            loc.updated_at = datetime.now(timezone.utc)
        else:
            loc = UserLocation(
                user_id=user_id,
                latitude=lat,
                longitude=lng,
                accuracy=data.accuracy,
            )
            self.session.add(loc)
        await self.session.commit()

        await redis.setex(
            LOCATION_KEY.format(str(user_id)),
            LOCATION_TTL,
            json.dumps({"lat": lat, "lng": lng, "updated_at": datetime.now(timezone.utc).isoformat()}),
        )

        friend_ids = await self.friend_service._friend_ids(user_id)
        for fid in friend_ids:
            await publish_to_user(
                redis,
                fid,
                {
                    "type": "location_update",
                    "user_id": str(user_id),
                    "lat": lat,
                    "lng": lng,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )

    async def get_ghost_mode(self, user_id: UUID) -> dict:
        result = await self.session.execute(
            select(UserLocation).where(UserLocation.user_id == user_id)
        )
        loc = result.scalar_one_or_none()
        return {"enabled": loc.ghost_mode if loc else False}

    async def set_ghost_mode(self, user_id: UUID, data: GhostModeUpdate) -> dict:
        result = await self.session.execute(
            select(UserLocation).where(UserLocation.user_id == user_id)
        )
        loc = result.scalar_one_or_none()
        if loc is None:
            loc = UserLocation(user_id=user_id, latitude=0, longitude=0, ghost_mode=data.enabled)
            self.session.add(loc)
        else:
            loc.ghost_mode = data.enabled
        await self.session.commit()
        return {"enabled": data.enabled}

    async def set_location_privacy(self, user_id: UUID, data: LocationPrivacyUpdate) -> None:
        result = await self.session.execute(
            select(UserLocation).where(UserLocation.user_id == user_id)
        )
        loc = result.scalar_one_or_none()
        if loc is None:
            loc = UserLocation(user_id=user_id, latitude=0, longitude=0, location_privacy=data.privacy)
            self.session.add(loc)
        else:
            loc.location_privacy = data.privacy
        await self.session.commit()

    async def get_friends_on_map(
        self, user_id: UUID, redis: aioredis.Redis | None
    ) -> list[SnapMapUser]:
        my_loc_result = await self.session.execute(
            select(UserLocation).where(UserLocation.user_id == user_id)
        )
        my_loc = my_loc_result.scalar_one_or_none()
        my_lat = my_loc.latitude if my_loc else None
        my_lng = my_loc.longitude if my_loc else None

        friend_ids = await self.friend_service._friend_ids(user_id)
        if not friend_ids:
            return []

        result = await self.session.execute(
            select(UserLocation, User)
            .join(User, User.id == UserLocation.user_id)
            .where(
                UserLocation.user_id.in_(friend_ids),
                UserLocation.ghost_mode.is_(False),
                UserLocation.location_privacy.in_(["everyone", "friends"]),
            )
        )

        users: list[SnapMapUser] = []
        for loc, user in result.all():
            distance = None
            if my_lat is not None and my_lng is not None:
                distance = round(_haversine_km(my_lat, my_lng, loc.latitude, loc.longitude), 1)
            users.append(
                SnapMapUser(
                    user_id=user.id,
                    name=user.full_name,
                    avatar_url=user.avatar_url,
                    lat=loc.latitude,
                    lng=loc.longitude,
                    distance_km=distance,
                    updated_at=loc.updated_at,
                )
            )
        return users

    async def update_profile(self, user_id: UUID, data: ProfileUpdate) -> UserProfile:
        profile = await self._get_or_create_profile(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_public_profile(
        self, target_id: UUID, viewer_id: UUID | None, redis: aioredis.Redis | None
    ) -> PublicProfileResponse:
        user = await self.user_repo.get_by_id(target_id)
        if user is None:
            raise NotFoundError("User not found")

        profile = await self._get_or_create_profile(target_id)
        is_friend = False
        request_sent = False
        request_received = False
        mutual_count = 0
        is_online = False

        if viewer_id:
            is_friend = await self.friend_service.are_friends(viewer_id, target_id)
            mutual = await self.friend_service.get_mutual_friends(viewer_id, target_id)
            mutual_count = mutual.count
            if redis:
                is_online = await OnlineStatusService(self.session).is_user_online(target_id, redis)

            from app.domains.friend.models import FriendRequest

            sent = await self.session.execute(
                select(FriendRequest).where(
                    FriendRequest.sender_id == viewer_id,
                    FriendRequest.receiver_id == target_id,
                    FriendRequest.status == "pending",
                )
            )
            request_sent = sent.scalar_one_or_none() is not None
            recv = await self.session.execute(
                select(FriendRequest).where(
                    FriendRequest.sender_id == target_id,
                    FriendRequest.receiver_id == viewer_id,
                    FriendRequest.status == "pending",
                )
            )
            request_received = recv.scalar_one_or_none() is not None

        return PublicProfileResponse(
            id=user.id,
            full_name=user.full_name,
            username=user.username,
            avatar_url=user.avatar_url,
            bio=profile.bio,
            game_tags=profile.game_tags,
            city=profile.city or user.city,
            is_private=profile.is_private,
            friends_count=user.friends_count,
            followers_count=user.followers_count,
            following_count=user.following_count,
            is_friend=is_friend,
            friend_request_sent=request_sent,
            friend_request_received=request_received,
            is_online=is_online,
            mutual_friends_count=mutual_count,
        )

    async def search_users(self, query: str, limit: int = 20) -> list[User]:
        pattern = f"%{query}%"
        result = await self.session.execute(
            select(User).where(
                or_(User.full_name.ilike(pattern), User.username.ilike(pattern))
            ).limit(limit)
        )
        return list(result.scalars().all())