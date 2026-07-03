"""GC Points loyalty API routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.gaming_booking.repository import GamingBookingRepository
from app.domains.gaming_booking.schemas import (
    GCPointsResponse,
    GCPointsTransactionResponse,
    GCPointsTransactionsResponse,
)

router = APIRouter(tags=["GC Points"])


@router.get("/users/me/gc-points", response_model=GCPointsResponse)
async def get_my_gc_points(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> GCPointsResponse:
    repo = GamingBookingRepository(db)
    points = await repo.get_gc_points(current_user.id)
    if points is None:
        return GCPointsResponse(
            user_id=current_user.id,
            balance=0,
            lifetime_earned=0,
            updated_at=datetime.now(UTC),
        )
    return GCPointsResponse.model_validate(points)


@router.get("/users/me/gc-points/transactions", response_model=GCPointsTransactionsResponse)
async def list_my_gc_points_transactions(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> GCPointsTransactionsResponse:
    repo = GamingBookingRepository(db)
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    offset = (page - 1) * limit
    txs, total = await repo.list_gc_transactions(
        current_user.id, limit=limit, offset=offset
    )
    return GCPointsTransactionsResponse(
        items=[GCPointsTransactionResponse.model_validate(t) for t in txs],
        total=total,
    )