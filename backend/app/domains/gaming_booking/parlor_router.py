"""OYO-style parlor discovery routes under /parlors."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import DbSessionDep, OptionalCurrentUserDep, RedisDep
from app.domains.gaming_booking.schemas import (
    OfferListResponse,
    ParlourDetailResponse,
    ParlourGalleryResponse,
    ParlourRatingsSummary,
    ParlourSearchResult,
    SlotListResponse,
)
from app.domains.gaming_booking.service import ParlourBookingViewService

router = APIRouter(prefix="/parlors", tags=["Gaming Parlors"])


@router.get("/search", response_model=ParlourSearchResult)
async def search_parlors_oyo(
    db: DbSessionDep,
    redis: RedisDep,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=5000, ge=100, le=50000),
    q: str | None = None,
    min_rating: float | None = Query(default=None, ge=0, le=5),
    open_now: bool | None = None,
    city: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: OptionalCurrentUserDep = None,
) -> ParlourSearchResult:
    user_id = current_user.id if current_user else None
    return await ParlourBookingViewService(db).search_parlors(
        lat,
        lng,
        radius_m=radius,
        q=q,
        min_rating=min_rating,
        open_now=open_now,
        city=city,
        page=page,
        limit=limit,
        user_id=user_id,
        redis=redis,
    )


@router.get("/{parlour_id}/detail", response_model=ParlourDetailResponse)
async def get_parlor_detail(
    parlour_id: UUID,
    db: DbSessionDep,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
) -> ParlourDetailResponse:
    return await ParlourBookingViewService(db).get_detail(parlour_id, lat=lat, lng=lng)


@router.get("/{parlour_id}/slots", response_model=SlotListResponse)
async def list_parlor_slots(
    parlour_id: UUID,
    db: DbSessionDep,
    slot_date: date | None = None,
) -> SlotListResponse:
    return await ParlourBookingViewService(db).get_slots(parlour_id, slot_date=slot_date)


@router.get("/{parlour_id}/offers", response_model=OfferListResponse)
async def list_parlor_offers(
    parlour_id: UUID,
    db: DbSessionDep,
) -> OfferListResponse:
    return await ParlourBookingViewService(db).get_offers(parlour_id)


@router.get("/{parlour_id}/gallery", response_model=ParlourGalleryResponse)
async def get_parlor_gallery(
    parlour_id: UUID,
    db: DbSessionDep,
) -> ParlourGalleryResponse:
    return await ParlourBookingViewService(db).get_gallery(parlour_id)


@router.get("/{parlour_id}/ratings", response_model=ParlourRatingsSummary)
async def get_parlor_ratings(
    parlour_id: UUID,
    db: DbSessionDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> ParlourRatingsSummary:
    return await ParlourBookingViewService(db).get_ratings(
        parlour_id, page=page, limit=limit
    )