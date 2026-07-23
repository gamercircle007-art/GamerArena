"""Parlor data access — backed by the ``gaming_places`` catalog."""

import math
from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_place.mappers import GamingPlaceView, to_view
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension


def _haversine_meters(
    lat: float, lng: float, place_lat: float, place_lng: float
) -> float:
    """Great-circle distance in meters (SQLite-safe; no SQL math functions)."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat), math.radians(place_lat)
    dphi = math.radians(place_lat - lat)
    dlambda = math.radians(place_lng - lng)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class ParlorRepository:
    """Repository for venue reads/writes via ``gaming_places``."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _is_sqlite(self) -> bool:
        return self.session.get_bind().dialect.name == "sqlite"

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
        view = await self._to_view(place)
        if view.is_deleted:
            return None
        return view

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
            .outerjoin(
                GamingPlaceExtension,
                GamingPlaceExtension.gaming_place_id == GamingPlace.id,
            )
            .where(
                or_(
                    GamingPlace.name.ilike(pattern),
                    GamingPlace.address.ilike(pattern),
                    GamingPlace.primary_type.ilike(pattern),
                ),
                or_(
                    GamingPlaceExtension.is_deleted.is_(False),
                    GamingPlaceExtension.gaming_place_id.is_(None),
                ),
            )
            .order_by(GamingPlace.name.asc())
            .limit(limit)
        )
        places = result.scalars().all()
        return [await self._to_view(place) for place in places]

    async def _places_with_coords(self) -> list[GamingPlace]:
        result = await self.session.execute(
            select(GamingPlace).where(
                GamingPlace.latitude.isnot(None),
                GamingPlace.longitude.isnot(None),
            )
        )
        return list(result.scalars().all())

    async def _distance_rows_sql(
        self,
        lat: float,
        lng: float,
        *,
        radius_m: float | None,
        fetch_limit: int,
    ) -> list[tuple[UUID, float]]:
        """Postgres Haversine via SQL math functions."""
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
            LIMIT :fetch_limit
            """
        )
        params: dict = {"lat": lat, "lng": lng, "fetch_limit": fetch_limit}
        if radius_m is not None:
            params["radius"] = radius_m
        result = await self.session.execute(sql, params)
        return [(UUID(str(row["id"])), float(row["distance_meters"])) for row in result.mappings()]

    async def _distance_rows_python(
        self,
        lat: float,
        lng: float,
        *,
        radius_m: float | None,
        fetch_limit: int,
    ) -> list[tuple[UUID, float]]:
        """SQLite / no-math-function dialects: compute Haversine in Python."""
        places = await self._places_with_coords()
        scored: list[tuple[UUID, float]] = []
        for place in places:
            if place.latitude is None or place.longitude is None:
                continue
            dist = _haversine_meters(lat, lng, float(place.latitude), float(place.longitude))
            if radius_m is not None and dist > radius_m:
                continue
            scored.append((place.id, dist))
        scored.sort(key=lambda item: item[1])
        return scored[:fetch_limit]

    async def _distance_rows(
        self,
        lat: float,
        lng: float,
        *,
        radius_m: float | None,
        fetch_limit: int,
    ) -> list[tuple[UUID, float]]:
        if self._is_sqlite():
            return await self._distance_rows_python(
                lat, lng, radius_m=radius_m, fetch_limit=fetch_limit
            )
        try:
            return await self._distance_rows_sql(
                lat, lng, radius_m=radius_m, fetch_limit=fetch_limit
            )
        except Exception:
            # Free-tier Postgres without PostGIS/math extensions
            return await self._distance_rows_python(
                lat, lng, radius_m=radius_m, fetch_limit=fetch_limit
            )

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
        rows = await self._distance_rows(
            lat, lng, radius_m=radius_m, fetch_limit=fetch_limit
        )
        if not rows:
            return [], 0

        place_ids = [place_id for place_id, _ in rows]
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
        for place_id, distance_meters in rows:
            place = places_by_id.get(place_id)
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
            filtered.append((place, view, float(distance_meters)))

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
        """Return venues with coordinates, sorted nearest-first (SQLite + Postgres)."""
        rows = await self._distance_rows(
            lat, lng, radius_m=radius_m, fetch_limit=limit
        )
        if not rows:
            return []

        place_ids = [place_id for place_id, _ in rows]
        places_result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id.in_(place_ids))
        )
        places_by_id = {place.id: place for place in places_result.scalars()}

        items: list[tuple[GamingPlace, GamingPlaceView, float]] = []
        for place_id, distance_meters in rows:
            place = places_by_id.get(place_id)
            if place is None:
                continue
            view = await self._to_view(place)
            items.append((place, view, float(distance_meters)))
        return items