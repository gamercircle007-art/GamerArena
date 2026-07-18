"""Feed domain business logic with Redis caching."""

import json
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domains.feed.demo_data import load_demo_feed
from app.domains.feed.schemas import FeedPostItem, FeedResponse, FeedTournamentItem
from app.domains.post.repository import PostRepository
from app.domains.post.service import PostService
from app.domains.tournament.models import Tournament
from app.domains.tournament.service import TournamentService

FEED_TTL_SECONDS = 60


class FeedService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.post_repo = PostRepository(session)
        self.post_service = PostService(session)
        self.tournament_service = TournamentService(session)

    async def build_feed(
        self,
        user_id: UUID,
        page: int,
        limit: int,
        redis: aioredis.Redis,
        *,
        user_lat: float | None = None,
        user_lng: float | None = None,
    ) -> FeedResponse:
        cache_key = f"feed:{user_id}:{page}:{limit}"
        cached = await redis.get(cache_key)
        if cached:
            return FeedResponse.model_validate_json(cached)

        offset = (page - 1) * limit
        posts = await self.post_repo.list_from_followed(user_id, limit=limit, offset=offset)
        items: list[FeedPostItem | FeedTournamentItem] = []  # noqa: UP007

        for post in posts:
            post_response = await self.post_service._to_response(post, user_id)
            items.append(FeedPostItem(data=post_response))

        if user_lat is not None and user_lng is not None and page == 1:
            tournaments = await self._nearby_open_tournaments(user_lat, user_lng, limit=5)
            for tournament in tournaments:
                t_response = await self.tournament_service._to_response(tournament, user_id)
                items.append(FeedTournamentItem(data=t_response))

        response = FeedResponse(items=items, page=page, limit=limit)
        if not response.items and get_settings().app_env == "local":
            demo = load_demo_feed()
            if page == 1:
                response = FeedResponse(
                    items=demo.items,
                    page=page,
                    limit=limit,
                )

        await redis.set(cache_key, response.model_dump_json(), ex=FEED_TTL_SECONDS)
        return response

    async def _nearby_open_tournaments(
        self,
        lat: float,
        lng: float,
        *,
        limit: int,
    ) -> list[Tournament]:
        sql = text(
            """
            SELECT t.id
            FROM tournaments t
            JOIN gaming_places gp ON gp.id = t.parlor_id
            JOIN (
                SELECT
                    gp2.id AS place_id,
                    (6371000 * acos(
                        LEAST(1.0, GREATEST(-1.0,
                            cos(radians(:lat)) * cos(radians(gp2.latitude))
                            * cos(radians(gp2.longitude) - radians(:lng))
                            + sin(radians(:lat)) * sin(radians(gp2.latitude))
                        ))
                    )) AS distance_meters
                FROM gaming_places gp2
                WHERE gp2.latitude IS NOT NULL AND gp2.longitude IS NOT NULL
            ) sub ON sub.place_id = gp.id
            WHERE t.status = 'open'
              AND sub.distance_meters <= :radius
            ORDER BY t.start_time ASC
            LIMIT :limit
            """
        )
        result = await self.session.execute(
            sql,
            {"lat": lat, "lng": lng, "radius": 10000, "limit": limit},
        )
        ids = [row["id"] for row in result.mappings().all()]
        if not ids:
            return []

        t_result = await self.session.execute(select(Tournament).where(Tournament.id.in_(ids)))
        return list(t_result.scalars().all())