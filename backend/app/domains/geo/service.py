"""Geo domain business logic — nearby venues from ``gaming_places``."""

import json
import math
from datetime import datetime

import redis.asyncio as aioredis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_place.location_utils import (
    extract_images,
    extract_locality,
    is_open_now,
)
from app.domains.gaming_place.models import GamingPlace
from app.domains.gaming_place.mappers import GamingPlaceView
from app.domains.geo.schemas import (
    NearbyParlorResponse,
    NearbyTournamentResponse,
    ParlorSearchResponse,
)
from app.domains.parlor.repository import ParlorRepository

GEO_CACHE_TTL = 120


class GeoService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.parlor_repo = ParlorRepository(session)

    def _to_parlor_response(
        self,
        place: GamingPlace,
        view: GamingPlaceView,
        distance: float,
    ) -> NearbyParlorResponse:
        city, state, country = extract_locality(place)
        images = extract_images(place)
        logo = view.logo_url or (images[0] if images else None)
        return NearbyParlorResponse(
            id=view.id,
            name=view.name,
            description=view.description,
            logo_url=logo,
            address=view.address,
            city=city,
            state=state,
            country=country,
            game_types=view.game_types,
            is_verified=view.is_verified,
            follower_count=view.follower_count,
            distance_meters=distance,
            lat=view.latitude,
            lng=view.longitude,
            rating=view.rating,
            phone=view.phone,
            website=view.website,
            is_open=is_open_now(place),
            images=images,
        )

    async def nearby_parlors(
        self,
        lat: float,
        lng: float,
        radius_m: float,
        *,
        game_type: str | None = None,
        limit: int = 20,
        redis: aioredis.Redis | None = None,
    ) -> list[NearbyParlorResponse]:
        cache_key = f"geo:parlors:{round(lat, 2)}:{round(lng, 2)}:{int(radius_m)}:{game_type}"
        if redis is not None:
            cached = await redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return [NearbyParlorResponse.model_validate(item) for item in data]

        rows, _ = await self.parlor_repo.search_nearby(
            lat,
            lng,
            radius_m=radius_m,
            game_type=game_type,
            limit=limit,
        )
        results = [
            self._to_parlor_response(place, view, distance)
            for place, view, distance in rows
        ]

        if redis is not None:
            await redis.set(
                cache_key,
                json.dumps([r.model_dump(mode="json") for r in results]),
                ex=GEO_CACHE_TTL,
            )
        return results

    async def search_parlors(
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
        page: int = 1,
        limit: int = 20,
        redis: aioredis.Redis | None = None,
    ) -> ParlorSearchResponse:
        page = max(page, 1)
        limit = min(max(limit, 1), 50)
        offset = (page - 1) * limit
        cache_key = (
            f"geo:search:{round(lat, 2)}:{round(lng, 2)}:{int(radius_m)}:"
            f"{q}:{min_rating}:{open_now}:{city}:{state}:{game_type}:{page}:{limit}"
        )
        if redis is not None:
            cached = await redis.get(cache_key)
            if cached:
                return ParlorSearchResponse.model_validate(json.loads(cached))

        rows, total = await self.parlor_repo.search_nearby(
            lat,
            lng,
            radius_m=radius_m,
            q=q,
            min_rating=min_rating,
            open_now=open_now,
            city=city,
            state=state,
            game_type=game_type,
            offset=offset,
            limit=limit,
        )
        items = [
            self._to_parlor_response(place, view, distance)
            for place, view, distance in rows
        ]
        response = ParlorSearchResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_more=(offset + len(items)) < total,
        )
        if redis is not None:
            await redis.set(
                cache_key,
                json.dumps(response.model_dump(mode="json")),
                ex=GEO_CACHE_TTL,
            )
        return response

    async def nearby_tournaments(
        self,
        lat: float,
        lng: float,
        radius_m: float,
        *,
        status: str | None = "open",
        date_from: datetime | None = None,
        limit: int = 20,
        redis: aioredis.Redis | None = None,
    ) -> list[NearbyTournamentResponse]:
        cache_key = (
            f"geo:tournaments:{round(lat, 2)}:{round(lng, 2)}:{int(radius_m)}:{status}:{date_from}"
        )
        if redis is not None:
            cached = await redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return [NearbyTournamentResponse.model_validate(item) for item in data]

        status_filter = "AND t.status = :status" if status else ""
        date_filter = "AND t.start_time >= :date_from" if date_from else ""
        params: dict = {
            "lat": lat,
            "lng": lng,
            "radius": radius_m,
            "limit": limit,
        }
        if status:
            params["status"] = status
        if date_from:
            params["date_from"] = date_from

        sql = text(
            f"""
            SELECT
                t.id, t.parlor_id, gp.name AS parlor_name, t.title, t.game_type,
                t.start_time, t.end_time, t.total_slots, t.booked_slots,
                t.entry_fee, t.status, sub.distance_meters
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
            WHERE sub.distance_meters <= :radius
              {status_filter}
              {date_filter}
            ORDER BY t.start_time ASC
            LIMIT :limit
            """
        )
        result = await self.session.execute(sql, params)
        rows = [NearbyTournamentResponse.model_validate(dict(row)) for row in result.mappings()]
        if redis is not None:
            await redis.set(
                cache_key,
                json.dumps([r.model_dump(mode="json") for r in rows]),
                ex=GEO_CACHE_TTL,
            )
        return rows

    async def _distance_meters(
        self, lat: float, lng: float, place_lat: float, place_lng: float
    ) -> float:
        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            try:
                sql = text(
                    """
                    SELECT ST_Distance(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(:place_lng, :place_lat), 4326)::geography
                    ) AS distance_meters
                    """
                )
                result = await self.session.execute(
                    sql,
                    {"lat": lat, "lng": lng, "place_lat": place_lat, "place_lng": place_lng},
                )
                return float(result.scalar_one())
            except Exception:
                # Free-tier Postgres without PostGIS — pure Haversine fallback
                return self._haversine_meters(lat, lng, place_lat, place_lng)

        return self._haversine_meters(lat, lng, place_lat, place_lng)

    @staticmethod
    def _haversine_meters(lat: float, lng: float, place_lat: float, place_lng: float) -> float:
        r = 6371000.0
        phi1, phi2 = math.radians(lat), math.radians(place_lat)
        dphi = math.radians(place_lat - lat)
        dlambda = math.radians(place_lng - lng)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    async def _postgis_nearby_rows(
        self,
        lat: float,
        lng: float,
        radius_m: float,
        *,
        limit: int = 20,
    ) -> list[tuple[GamingPlace, GamingPlaceView, float]]:
        bind = self.session.get_bind()
        if bind.dialect.name != "postgresql":
            items, _ = await self.parlor_repo.search_nearby(
                lat, lng, radius_m=radius_m, limit=limit
            )
            return [(place, view, distance) for place, view, distance in items]

        try:
            sql = text(
                """
                SELECT
                    gp.id,
                    ST_Distance(
                        ST_SetSRID(ST_MakePoint(gp.longitude, gp.latitude), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                    ) AS distance_meters
                FROM gaming_places gp
                WHERE gp.latitude IS NOT NULL
                  AND gp.longitude IS NOT NULL
                  AND ST_DWithin(
                        ST_SetSRID(ST_MakePoint(gp.longitude, gp.latitude), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                        :radius
                  )
                ORDER BY distance_meters ASC
                LIMIT :limit
                """
            )
            result = await self.session.execute(
                sql, {"lat": lat, "lng": lng, "radius": radius_m, "limit": limit}
            )
            mappings = result.mappings().all()
        except Exception:
            # No PostGIS: fall back to haversine search
            items, _ = await self.parlor_repo.search_nearby(
                lat, lng, radius_m=radius_m, limit=limit
            )
            return [(place, view, distance) for place, view, distance in items]

        if not mappings:
            return []

        from uuid import UUID

        place_ids = [UUID(str(row["id"])) for row in mappings]
        places_result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id.in_(place_ids))
        )
        places_by_id = {place.id: place for place in places_result.scalars()}

        rows: list[tuple[GamingPlace, GamingPlaceView, float]] = []
        for row in mappings:
            place = places_by_id.get(UUID(str(row["id"])))
            if place is None:
                continue
            view = await self.parlor_repo._to_view(place)
            rows.append((place, view, float(row["distance_meters"])))
        return rows

    async def get_nearby_parlors_sorted(
        self,
        lat: float,
        lng: float,
        radius_m: float,
        *,
        limit: int = 20,
        redis: aioredis.Redis | None = None,
    ) -> list[tuple[GamingPlace, GamingPlaceView, float]]:
        cache_key = (
            f"geo:nearby_sorted:{round(lat, 2)}:{round(lng, 2)}:{int(radius_m)}:{limit}"
        )
        if redis is not None:
            cached = await redis.get(cache_key)
            if cached:
                payload = json.loads(cached)
                from uuid import UUID

                ids = [UUID(item["id"]) for item in payload]
                places_result = await self.session.execute(
                    select(GamingPlace).where(GamingPlace.id.in_(ids))
                )
                places_by_id = {p.id: p for p in places_result.scalars()}
                rows = []
                for item in payload:
                    place = places_by_id.get(UUID(item["id"]))
                    if place is None:
                        continue
                    view = await self.parlor_repo._to_view(place)
                    rows.append((place, view, float(item["distance_meters"])))
                return rows

        rows = await self._postgis_nearby_rows(lat, lng, radius_m, limit=limit)
        if redis is not None:
            await redis.set(
                cache_key,
                json.dumps(
                    [
                        {"id": str(place.id), "distance_meters": distance}
                        for place, _, distance in rows
                    ]
                ),
                ex=GEO_CACHE_TTL,
            )
        return rows

    async def get_nearby_count(
        self,
        lat: float,
        lng: float,
        radius_m: float,
        *,
        redis: aioredis.Redis | None = None,
    ) -> int:
        cache_key = f"geo:nearby_count:{round(lat, 2)}:{round(lng, 2)}:{int(radius_m)}"
        if redis is not None:
            cached = await redis.get(cache_key)
            if cached is not None:
                return int(cached)

        bind = self.session.get_bind()
        if bind.dialect.name == "postgresql":
            sql = text(
                """
                SELECT COUNT(*) FROM gaming_places gp
                WHERE gp.latitude IS NOT NULL
                  AND gp.longitude IS NOT NULL
                  AND ST_DWithin(
                        ST_SetSRID(ST_MakePoint(gp.longitude, gp.latitude), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                        :radius
                  )
                """
            )
            count = int(
                await self.session.scalar(sql, {"lat": lat, "lng": lng, "radius": radius_m}) or 0
            )
        else:
            _, count = await self.parlor_repo.search_nearby(lat, lng, radius_m=radius_m, limit=1)

        if redis is not None:
            await redis.set(cache_key, str(count), ex=GEO_CACHE_TTL)
        return count

    async def get_city_parlors(
        self,
        city: str,
        *,
        limit: int = 20,
        redis: aioredis.Redis | None = None,
    ) -> list[tuple[GamingPlace, GamingPlaceView]]:
        cache_key = f"geo:city:{city.strip().lower()}:{limit}"
        if redis is not None:
            cached = await redis.get(cache_key)
            if cached:
                from uuid import UUID

                ids = [UUID(i) for i in json.loads(cached)]
                result = await self.session.execute(
                    select(GamingPlace).where(GamingPlace.id.in_(ids))
                )
                places = {p.id: p for p in result.scalars()}
                return [
                    (places[i], await self.parlor_repo._to_view(places[i]))
                    for i in ids
                    if i in places
                ]

        needle = city.strip().lower()
        result = await self.session.execute(
            select(GamingPlace)
            .where(
                func.lower(GamingPlace.address).contains(needle)
                | func.lower(GamingPlace.name).contains(needle)
            )
            .order_by(GamingPlace.rating.desc().nullslast(), GamingPlace.name.asc())
            .limit(limit)
        )
        places = list(result.scalars().all())
        rows = [(place, await self.parlor_repo._to_view(place)) for place in places]

        if redis is not None:
            await redis.set(
                cache_key,
                json.dumps([str(place.id) for place, _ in rows]),
                ex=GEO_CACHE_TTL,
            )
        return rows