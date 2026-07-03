"""Home page aggregation — nearby parlors, quick picks, cities."""

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_booking.repository import GamingBookingRepository
from app.domains.gaming_place.location_utils import extract_images, extract_locality
from app.domains.gaming_place.mappers import resolve_media_url
from app.domains.geo.service import GeoService
from app.domains.home.schemas import CitiesResponse, CityItem, HomeParlorCard, HomeResponse


class HomeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.geo = GeoService(session)
        self.repo = GamingBookingRepository(session)

    async def _to_card_async(
        self,
        place,
        view,
        *,
        distance: float | None = None,
    ) -> HomeParlorCard:
        ext = await self.repo.get_extension(place.id)
        city, _, _ = extract_locality(place)
        images = extract_images(place)
        return HomeParlorCard(
            id=view.id,
            name=view.name,
            image_url=resolve_media_url(place.image_url) or (images[0] if images else None),
            rating=view.rating,
            price_per_hour=ext.price_per_hour if ext else None,
            original_price=ext.original_price if ext else None,
            discount_percent=ext.discount_percent if ext else None,
            distance_meters=distance,
            city=city,
            is_verified=view.is_verified,
        )

    async def get_home(
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        city: str | None = None,
        radius_m: float = 5000,
        redis: aioredis.Redis | None = None,
    ) -> HomeResponse:
        nearby_count = 0
        featured: list[HomeParlorCard] = []
        quick_picks: list[HomeParlorCard] = []

        if lat is not None and lng is not None:
            nearby_count = await self.geo.get_nearby_count(lat, lng, radius_m, redis=redis)
            rows = await self.geo.get_nearby_parlors_sorted(
                lat, lng, radius_m, limit=10, redis=redis
            )
            featured = [await self._to_card_async(place, view, distance=d) for place, view, d in rows[:6]]
            quick_picks = [
                await self._to_card_async(place, view, distance=d) for place, view, d in rows[6:10]
            ]
        elif city:
            city_rows = await self.geo.get_city_parlors(city, limit=10, redis=redis)
            featured = [await self._to_card_async(place, view) for place, view in city_rows[:6]]
            quick_picks = [await self._to_card_async(place, view) for place, view in city_rows[6:10]]
            nearby_count = len(city_rows)

        return HomeResponse(
            nearby_count=nearby_count,
            featured=featured,
            quick_picks=quick_picks,
            city=city,
        )

    async def get_nearby(
        self,
        lat: float,
        lng: float,
        *,
        radius_m: float = 5000,
        limit: int = 20,
        redis: aioredis.Redis | None = None,
    ) -> list[HomeParlorCard]:
        rows = await self.geo.get_nearby_parlors_sorted(
            lat, lng, radius_m, limit=limit, redis=redis
        )
        return [await self._to_card_async(place, view, distance=d) for place, view, d in rows]

    async def get_quick_picks(
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        city: str | None = None,
        limit: int = 8,
        redis: aioredis.Redis | None = None,
    ) -> list[HomeParlorCard]:
        if lat is not None and lng is not None:
            rows = await self.geo.get_nearby_parlors_sorted(
                lat, lng, 10000, limit=limit, redis=redis
            )
            return [await self._to_card_async(place, view, distance=d) for place, view, d in rows]
        if city:
            rows = await self.geo.get_city_parlors(city, limit=limit, redis=redis)
            return [await self._to_card_async(place, view) for place, view in rows]
        return []

    async def get_cities(self, *, limit: int = 50) -> CitiesResponse:
        from app.domains.gaming_place.models import GamingPlace

        result = await self.session.execute(
            select(GamingPlace.address, func.count())
            .where(GamingPlace.address.isnot(None))
            .group_by(GamingPlace.address)
            .limit(500)
        )
        city_counts: dict[str, int] = {}
        for address, _ in result.all():
            if not address:
                continue
            parts = [p.strip() for p in address.split(",")]
            city_name = parts[-2] if len(parts) >= 2 else parts[0]
            if city_name:
                key = city_name.strip()
                city_counts[key] = city_counts.get(key, 0) + 1

        sorted_cities = sorted(city_counts.items(), key=lambda x: (-x[1], x[0]))[:limit]
        return CitiesResponse(
            cities=[CityItem(name=name, parlour_count=count) for name, count in sorted_cities]
        )