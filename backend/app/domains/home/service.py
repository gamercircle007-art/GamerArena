"""Home page aggregation — nearby parlors, quick picks, cities."""

from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_booking.repository import GamingBookingRepository
from app.domains.gaming_place.location_utils import extract_images, extract_locality
from app.domains.gaming_place.mappers import resolve_media_url
from app.domains.gaming_place.models import GamingPlace
from app.domains.geo.service import GeoService
from app.domains.parlor.repository import ParlorRepository
from app.domains.home.city_catalog import FEATURED_CITIES
from app.domains.gaming_booking.schemas import HomePostItem
from app.domains.home.schemas import CitiesResponse, CityItem, HomeParlorCard, HomeResponse
from app.domains.post.repository import PostRepository
from app.domains.post.service import PostService

PICK_FILTERS = frozenset({"recommended", "past_stays", "recently_viewed"})


class HomeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.geo = GeoService(session)
        self.repo = GamingBookingRepository(session)
        self.parlor_repo = ParlorRepository(session)

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

    async def _cards_for_places(
        self,
        rows: list[tuple],
        *,
        with_distance: bool = False,
    ) -> list[HomeParlorCard]:
        cards: list[HomeParlorCard] = []
        for row in rows:
            if with_distance:
                place, view, distance = row
                cards.append(await self._to_card_async(place, view, distance=distance))
            else:
                place, view = row
                cards.append(await self._to_card_async(place, view))
        return cards

    async def _cards_for_ids(
        self,
        parlour_ids: list[UUID],
        *,
        lat: float | None = None,
        lng: float | None = None,
    ) -> list[HomeParlorCard]:
        if not parlour_ids:
            return []
        result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id.in_(parlour_ids))
        )
        places_by_id = {place.id: place for place in result.scalars()}
        cards: list[HomeParlorCard] = []
        for parlour_id in parlour_ids:
            place = places_by_id.get(parlour_id)
            if place is None:
                continue
            view = await self.parlor_repo._to_view(place)
            distance = None
            if lat is not None and lng is not None and place.latitude and place.longitude:
                distance = await self.geo._distance_meters(
                    lat, lng, place.latitude, place.longitude
                )
            cards.append(await self._to_card_async(place, view, distance=distance))
        return cards

    async def get_quick_picks_filtered(
        self,
        *,
        pick_filter: str = "recommended",
        user_id: UUID | None = None,
        lat: float | None = None,
        lng: float | None = None,
        city: str | None = None,
        limit: int = 12,
        redis: aioredis.Redis | None = None,
    ) -> list[HomeParlorCard]:
        pick_filter = pick_filter if pick_filter in PICK_FILTERS else "recommended"

        if pick_filter == "past_stays":
            if user_id is None:
                return []
            parlour_ids = await self.repo.get_past_stay_parlour_ids(user_id, limit=limit)
            return await self._cards_for_ids(parlour_ids, lat=lat, lng=lng)

        if pick_filter == "recently_viewed":
            if user_id is None:
                return []
            parlour_ids = await self.repo.get_recently_viewed_parlour_ids(user_id, limit=limit)
            return await self._cards_for_ids(parlour_ids, lat=lat, lng=lng)

        if lat is not None and lng is not None:
            rows = await self.geo.get_nearby_parlors_sorted(
                lat, lng, 10000, limit=limit, redis=redis
            )
            return await self._cards_for_places(rows, with_distance=True)
        if city:
            rows = await self.geo.get_city_parlors(city, limit=limit, redis=redis)
            return await self._cards_for_places(rows)
        return []

    async def get_home(
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        city: str | None = None,
        radius_m: float | None = None,
        pick_filter: str = "recommended",
        user_id: UUID | None = None,
        redis: aioredis.Redis | None = None,
    ) -> HomeResponse:
        nearby_count = 0
        featured: list[HomeParlorCard] = []
        quick_picks = await self.get_quick_picks_filtered(
            pick_filter=pick_filter,
            user_id=user_id,
            lat=lat,
            lng=lng,
            city=city,
            limit=12,
            redis=redis,
        )

        nearby_parlors: list[HomeParlorCard] = []
        if lat is not None and lng is not None:
            all_rows = await self.parlor_repo.list_sorted_by_haversine(
                lat,
                lng,
                radius_m=radius_m,
                limit=500,
            )
            nearby_parlors = await self._cards_for_places(all_rows, with_distance=True)
            nearby_count = len(all_rows) if radius_m is None else await self.geo.get_nearby_count(
                lat, lng, radius_m, redis=redis
            )
            featured_radius = radius_m if radius_m is not None else 10000
            rows = await self.geo.get_nearby_parlors_sorted(
                lat, lng, featured_radius, limit=10, redis=redis
            )
            featured = await self._cards_for_places(rows[:6], with_distance=True)
        elif city:
            city_rows = await self.geo.get_city_parlors(city, limit=500, redis=redis)
            featured = await self._cards_for_places(city_rows[:6])
            nearby_count = len(city_rows)
            if lat is not None and lng is not None:
                all_rows = await self.parlor_repo.list_sorted_by_haversine(
                    lat,
                    lng,
                    radius_m=radius_m,
                    limit=500,
                )
                city_ids = {place.id for place, _ in city_rows}
                filtered_rows = [row for row in all_rows if row[0].id in city_ids]
                if not filtered_rows:
                    filtered_rows = [
                        (
                            place,
                            view,
                            await self.geo._distance_meters(
                                lat, lng, place.latitude or lat, place.longitude or lng
                            ),
                        )
                        for place, view in city_rows
                        if place.latitude is not None and place.longitude is not None
                    ]
                    filtered_rows.sort(key=lambda row: row[2])
                nearby_parlors = await self._cards_for_places(filtered_rows, with_distance=True)
            else:
                nearby_parlors = await self._cards_for_places(city_rows)

        cities = await self.get_cities(limit=50)
        posts = await self._get_home_posts(city=city, user_id=user_id)
        return HomeResponse(
            nearby_count=nearby_count,
            featured=featured,
            quick_picks=quick_picks,
            nearby_parlors=nearby_parlors,
            city=city,
            cities=cities.cities,
            pick_filter=pick_filter if pick_filter in PICK_FILTERS else "recommended",
            radius_meters=radius_m if lat is not None and lng is not None else None,
            posts=posts,
        )

    async def _get_home_posts(
        self,
        *,
        city: str | None = None,
        user_id: UUID | None = None,
        limit: int = 20,
    ) -> list[HomePostItem]:
        post_repo = PostRepository(self.session)
        post_service = PostService(self.session)
        try:
            rows = await post_repo.list_recent(limit=limit, city=city)
        except Exception:
            return []
        items: list[HomePostItem] = []
        for post in rows:
            try:
                response = await post_service._to_response(post, user_id)
            except Exception:
                continue
            items.append(
                HomePostItem(
                    id=response.id,
                    content=response.content,
                    media_urls=response.media_urls,
                    parlor_id=response.parlor.id,
                    parlor_name=response.parlor.name,
                    parlor_logo_url=response.parlor.logo_url,
                    parlor_verified=response.parlor.is_verified,
                    likes_count=response.likes_count,
                    comments_count=response.comments_count,
                    created_at=response.created_at,
                )
            )
        return items

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
        return await self._cards_for_places(rows, with_distance=True)

    async def get_quick_picks(
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        city: str | None = None,
        pick_filter: str = "recommended",
        user_id: UUID | None = None,
        limit: int = 8,
        redis: aioredis.Redis | None = None,
    ) -> list[HomeParlorCard]:
        return await self.get_quick_picks_filtered(
            pick_filter=pick_filter,
            user_id=user_id,
            lat=lat,
            lng=lng,
            city=city,
            limit=limit,
            redis=redis,
        )

    async def get_cities(self, *, limit: int = 50) -> CitiesResponse:
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

        featured_by_name = {item.name.lower(): item for item in FEATURED_CITIES}
        merged: dict[str, CityItem] = {}

        for featured in FEATURED_CITIES:
            count = 0
            for name, value in city_counts.items():
                if featured.name.lower() in name.lower():
                    count += value
            merged[featured.name.lower()] = featured.model_copy(update={"parlour_count": count})

        sorted_db = sorted(city_counts.items(), key=lambda x: (-x[1], x[0]))
        for name, count in sorted_db:
            key = name.lower()
            if key in merged:
                merged[key] = merged[key].model_copy(update={"parlour_count": count})
                continue
            if len(merged) >= limit:
                break
            merged[key] = CityItem(name=name, parlour_count=count)

        ordered: list[CityItem] = []
        for featured in FEATURED_CITIES:
            item = merged.pop(featured.name.lower(), None)
            if item is not None:
                ordered.append(item)
        ordered.extend(
            sorted(merged.values(), key=lambda item: (-item.parlour_count, item.name))
        )
        return CitiesResponse(cities=ordered[:limit])