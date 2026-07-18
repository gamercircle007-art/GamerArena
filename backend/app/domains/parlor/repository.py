"""Parlor data access — backed by the ``gaming_places`` catalog."""

from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_place.mappers import GamingPlaceView, to_view
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension


class ParlorRepository:
    """Repository for venue reads/writes via ``gaming_places``."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_extension(self, gaming_place_id: UUID) -> GamingPlaceExtension | None:
        result = await self.session.execute(
            select(GamingPlaceExtension).where(
                GamingPlaceExtension.gaming_place_id == gaming_place_id
            )
        )
        return result.scalar_one_or_none()

    async def _ensure_extension(self, gaming_place_id: UUID) -> GamingPlaceExtension:
        ext = await self._get_extension(gaming_place_id)
        if ext is not None:
            return ext
        ext = GamingPlaceExtension(gaming_place_id=gaming_place_id)
        self.session.add(ext)
        await self.session.flush()
        return ext

    async def _to_view(self, place: GamingPlace) -> GamingPlaceView:
        ext = await self._get_extension(place.id)
        return to_view(place, ext)

    async def get_by_id(self, parlor_id: UUID) -> GamingPlaceView | None:
        result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id == parlor_id)
        )
        place = result.scalar_one_or_none()
        if place is None:
            return None
        return await self._to_view(place)

    async def get_place_by_id(self, parlor_id: UUID) -> GamingPlace | None:
        result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id == parlor_id)
        )
        return result.scalar_one_or_none()

    async def get_by_owner_id(self, owner_id: UUID) -> GamingPlaceView | None:
        result = await self.session.execute(
            select(GamingPlace, GamingPlaceExtension)
            .join(
                GamingPlaceExtension,
                GamingPlaceExtension.gaming_place_id == GamingPlace.id,
            )
            .where(GamingPlaceExtension.owner_id == owner_id)
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None
        place, ext = row
        return to_view(place, ext)

    async def is_owned_by(self, parlor_id: UUID, owner_id: UUID) -> bool:
        result = await self.session.execute(
            select(GamingPlaceExtension.owner_id).where(
                GamingPlaceExtension.gaming_place_id == parlor_id,
                GamingPlaceExtension.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def increment_follower_count(self, parlor_id: UUID, delta: int) -> None:
        ext = await self._ensure_extension(parlor_id)
        ext.follower_count = max(0, ext.follower_count + delta)

    async def increment_post_count(self, parlor_id: UUID, delta: int) -> None:
        ext = await self._ensure_extension(parlor_id)
        ext.post_count = max(0, ext.post_count + delta)

    async def search(self, pattern: str, *, limit: int) -> list[GamingPlaceView]:
        result = await self.session.execute(
            select(GamingPlace)
            .where(
                or_(
                    GamingPlace.name.ilike(pattern),
                    GamingPlace.address.ilike(pattern),
                    GamingPlace.primary_type.ilike(pattern),
                )
            )
            .order_by(GamingPlace.name.asc())
            .limit(limit)
        )
        places = result.scalars().all()
        return [await self._to_view(place) for place in places]

    async def search_nearby(
        self,
        lat: float,
        lng: float,
        *,
        radius_m: float = 5000,
        q: str | None = None,
        min_rating: float | None = None,
        open_now: bool | None = None,
        city: str | None = None,
        state: str | None = None,
        game_type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[tuple[GamingPlace, GamingPlaceView, float]], int]:
        """Location-first search with text and filter support."""
        fetch_limit = min(max((limit + offset) * 4, 50), 200)
        sql = text(
            """
            SELECT id, distance_meters FROM (
                SELECT
                    gp.id AS id,
                    (6371000 * acos(
                        LEAST(1.0, GREATEST(-1.0,
                            cos(radians(:lat)) * cos(radians(gp.latitude))
                            * cos(radians(gp.longitude) - radians(:lng))
                            + sin(radians(:lat)) * sin(radians(gp.latitude))
                        ))
                    )) AS distance_meters
                FROM gaming_places gp
                WHERE gp.latitude IS NOT NULL
                  AND gp.longitude IS NOT NULL
            )
            WHERE distance_meters <= :radius
            ORDER BY distance_meters ASC
            LIMIT :fetch_limit
            """
        )
        result = await self.session.execute(
            sql,
            {
                "lat": lat,
                "lng": lng,
                "radius": radius_m,
                "fetch_limit": fetch_limit,
            },
        )
        rows = result.mappings().all()
        if not rows:
            return [], 0

        place_ids = [UUID(str(row["id"])) for row in rows]
        places_result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id.in_(place_ids))
        )
        places_by_id = {place.id: place for place in places_result.scalars()}

        from app.domains.gaming_place.location_utils import (
            extract_locality,
            is_open_now,
        )

        needle = q.strip().lower() if q else None
        game_needle = game_type.upper() if game_type else None
        city_needle = city.strip().lower() if city else None
        state_needle = state.strip().lower() if state else None

        filtered: list[tuple[GamingPlace, GamingPlaceView, float]] = []
        for row in rows:
            place = places_by_id.get(UUID(str(row["id"])))
            if place is None:
                continue
            if min_rating is not None and (place.rating or 0) < min_rating:
                continue
            if open_now is True and not is_open_now(place):
                continue

            locality_city, locality_state, _ = extract_locality(place)
            if city_needle:
                hay = f"{locality_city or ''} {place.address or ''}".lower()
                if city_needle not in hay:
                    continue
            if state_needle:
                hay = f"{locality_state or ''} {place.address or ''}".lower()
                if state_needle not in hay:
                    continue
            if needle:
                haystack = " ".join(
                    filter(
                        None,
                        [
                            place.name,
                            place.address,
                            locality_city,
                            locality_state,
                            place.primary_type,
                        ],
                    )
                ).lower()
                if needle not in haystack:
                    continue

            view = await self._to_view(place)
            if game_needle and not any(
                game_needle in g or g in game_needle for g in view.game_types
            ):
                continue
            filtered.append((place, view, float(row["distance_meters"])))

        total = len(filtered)
        page_items = filtered[offset : offset + limit]
        return page_items, total

    async def nearby(
        self,
        lat: float,
        lng: float,
        radius_m: float,
        *,
        game_type: str | None = None,
        limit: int = 20,
    ) -> list[tuple[GamingPlaceView, float]]:
        items, _ = await self.search_nearby(
            lat,
            lng,
            radius_m=radius_m,
            game_type=game_type,
            limit=limit,
        )
        return [(view, distance) for _, view, distance in items]

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(GamingPlace))
        return int(result.scalar_one())

    async def list_sorted_by_haversine(
        self,
        lat: float,
        lng: float,
        *,
        radius_m: float | None = None,
        limit: int = 500,
    ) -> list[tuple[GamingPlace, GamingPlaceView, float]]:
        """Return all venues with coordinates, sorted nearest-first via Haversine."""
        radius_clause = "WHERE distance_meters <= :radius" if radius_m is not None else ""
        sql = text(
            f"""
            SELECT id, distance_meters FROM (
                SELECT
                    gp.id AS id,
                    (6371000 * acos(
                        LEAST(1.0, GREATEST(-1.0,
                            cos(radians(:lat)) * cos(radians(gp.latitude))
                            * cos(radians(gp.longitude) - radians(:lng))
                            + sin(radians(:lat)) * sin(radians(gp.latitude))
                        ))
                    )) AS distance_meters
                FROM gaming_places gp
                WHERE gp.latitude IS NOT NULL
                  AND gp.longitude IS NOT NULL
            ) AS nearby_sub
            {radius_clause}
            ORDER BY distance_meters ASC
            LIMIT :limit
            """
        )
        params: dict = {"lat": lat, "lng": lng, "limit": limit}
        if radius_m is not None:
            params["radius"] = radius_m

        result = await self.session.execute(sql, params)
        rows = result.mappings().all()
        if not rows:
            return []

        place_ids = [UUID(str(row["id"])) for row in rows]
        places_result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id.in_(place_ids))
        )
        places_by_id = {place.id: place for place in places_result.scalars()}

        items: list[tuple[GamingPlace, GamingPlaceView, float]] = []
        for row in rows:
            place = places_by_id.get(UUID(str(row["id"])))
            if place is None:
                continue
            view = await self._to_view(place)
            items.append((place, view, float(row["distance_meters"])))
        return items