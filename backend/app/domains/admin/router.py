"""Admin panel API — stats, users, and moderation endpoints."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.gaming_booking.gc_points import GCPointsTransaction
from app.domains.gaming_booking.models import GamingSlot, ParlourOffer
from app.domains.gaming_booking.repository import GamingBookingRepository
from app.domains.gaming_booking.schemas import (
    AdminGCPointsAdjust,
    AdminOfferCreate,
    AdminSlotCreate,
    GamingBookingResponse,
    GamingSlotResponse,
    ParlourOfferResponse,
)
from app.domains.gaming_booking.service import GamingBookingService
from app.domains.parlor.models import Parlor
from app.domains.user.models import User, UserRole
from app.domains.user.schemas import UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


def _require_admin(user) -> None:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


def _paginated(items: list, total: int, page: int, limit: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": page * limit < total,
    }


@router.get("/stats")
async def admin_stats(
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)

    users_count = await db.scalar(select(func.count()).select_from(User)) or 0
    parlors_count = await db.scalar(select(func.count()).select_from(Parlor)) or 0
    pending_verification = await db.scalar(
        select(func.count()).select_from(Parlor).where(Parlor.is_verified.is_(False))
    ) or 0

    return {
        "users": users_count,
        "parlors": parlors_count,
        "tournaments": 0,
        "bookings": 0,
        "posts": 0,
        "revenue": 0,
        "new_users_today": 0,
        "pending_verification": pending_verification,
    }


@router.get("/users")
async def admin_list_users(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> dict:
    _require_admin(current_user)

    page = max(1, page)
    limit = min(max(1, limit), 100)
    query = select(User)

    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.full_name.ilike(term),
                User.username.ilike(term),
                User.email.ilike(term),
                User.phone.ilike(term),
            )
        )

    if role:
        try:
            query = query.where(User.role == UserRole(role))
        except ValueError:
            pass

    if is_active is not None:
        query = query.where(User.is_active.is_(is_active))

    count_query = select(func.count()).select_from(User)
    if search:
        term = f"%{search.strip()}%"
        count_query = count_query.where(
            or_(
                User.full_name.ilike(term),
                User.username.ilike(term),
                User.email.ilike(term),
                User.phone.ilike(term),
            )
        )
    if role:
        try:
            count_query = count_query.where(User.role == UserRole(role))
        except ValueError:
            pass
    if is_active is not None:
        count_query = count_query.where(User.is_active.is_(is_active))

    total = await db.scalar(count_query) or 0
    result = await db.execute(
        query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    users = result.scalars().all()
    items = [UserResponse.model_validate(u).model_dump(mode="json") for u in users]

    return _paginated(items, total, page, limit)


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_validate(user).model_dump(mode="json")


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: UUID,
    body: dict,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if "is_active" in body:
        user.is_active = bool(body["is_active"])
    if "role" in body:
        try:
            user.role = UserRole(body["role"])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role") from exc

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user).model_dump(mode="json")


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)

    if str(current_user.id) == str(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(user)
    await db.commit()


# --- Gaming bookings (OYO-style) ---


@router.get("/gaming-bookings")
async def admin_list_gaming_bookings(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    parlour_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = 1,
    limit: int = 20,
) -> dict:
    _require_admin(current_user)
    page = max(1, page)
    limit = min(max(1, limit), 100)
    repo = GamingBookingRepository(db)
    bookings, total = await repo.list_all_bookings(
        parlour_id=parlour_id,
        status=status_filter,
        limit=limit,
        offset=(page - 1) * limit,
    )
    service = GamingBookingService(db)
    items = [await service._to_response(b) for b in bookings]
    return _paginated(
        [i.model_dump(mode="json") for i in items],
        total,
        page,
        limit,
    )


@router.get("/gaming-bookings/{booking_id}", response_model=GamingBookingResponse)
async def admin_get_gaming_booking(
    booking_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> GamingBookingResponse:
    _require_admin(current_user)
    return await GamingBookingService(db).get_booking(booking_id)


@router.get("/gaming-offers")
async def admin_list_gaming_offers(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    parlour_id: UUID | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    _require_admin(current_user)
    page = max(1, page)
    limit = min(max(1, limit), 100)
    query = select(ParlourOffer)
    if parlour_id:
        query = query.where(ParlourOffer.parlour_id == parlour_id)
    count_q = select(func.count()).select_from(ParlourOffer)
    if parlour_id:
        count_q = count_q.where(ParlourOffer.parlour_id == parlour_id)
    total = await db.scalar(count_q) or 0
    result = await db.execute(
        query.order_by(ParlourOffer.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    offers = result.scalars().all()
    items = [ParlourOfferResponse.model_validate(o).model_dump(mode="json") for o in offers]
    return _paginated(items, int(total), page, limit)


@router.post("/gaming-offers", response_model=ParlourOfferResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_gaming_offer(
    body: AdminOfferCreate,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> ParlourOfferResponse:
    _require_admin(current_user)
    offer = ParlourOffer(
        id=uuid4(),
        parlour_id=body.parlour_id,
        title=body.title,
        description=body.description,
        code=body.code,
        discount_percent=body.discount_percent,
        discount_amount=body.discount_amount,
        min_hours=body.min_hours,
        max_uses=body.max_uses,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        is_active=body.is_active,
    )
    repo = GamingBookingRepository(db)
    await repo.create_offer(offer)
    await db.commit()
    await db.refresh(offer)
    return ParlourOfferResponse.model_validate(offer)


@router.get("/gaming-slots")
async def admin_list_gaming_slots(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    parlour_id: UUID | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    _require_admin(current_user)
    page = max(1, page)
    limit = min(max(1, limit), 100)
    query = select(GamingSlot)
    if parlour_id:
        query = query.where(GamingSlot.parlour_id == parlour_id)
    count_q = select(func.count()).select_from(GamingSlot)
    if parlour_id:
        count_q = count_q.where(GamingSlot.parlour_id == parlour_id)
    total = await db.scalar(count_q) or 0
    result = await db.execute(
        query.order_by(GamingSlot.slot_date.desc(), GamingSlot.start_time.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    slots = result.scalars().all()
    items = [GamingSlotResponse.model_validate(s).model_dump(mode="json") for s in slots]
    return _paginated(items, int(total), page, limit)


@router.post("/gaming-slots", response_model=GamingSlotResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_gaming_slot(
    body: AdminSlotCreate,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> GamingSlotResponse:
    _require_admin(current_user)
    slot = GamingSlot(
        id=uuid4(),
        parlour_id=body.parlour_id,
        slot_date=body.slot_date,
        start_time=body.start_time,
        end_time=body.end_time,
        price_per_hour=body.price_per_hour,
        original_price=body.original_price,
        max_players=body.max_players,
    )
    repo = GamingBookingRepository(db)
    await repo.create_slot(slot)
    await db.commit()
    await db.refresh(slot)
    return GamingSlotResponse.model_validate(slot)


@router.get("/gc-points/{user_id}")
async def admin_get_user_gc_points(
    user_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    repo = GamingBookingRepository(db)
    points = await repo.get_gc_points(user_id)
    if points is None:
        return {
            "user_id": str(user_id),
            "balance": 0,
            "lifetime_earned": 0,
            "updated_at": datetime.now(UTC).isoformat(),
        }
    return {
        "user_id": str(points.user_id),
        "balance": points.balance,
        "lifetime_earned": points.lifetime_earned,
        "updated_at": points.updated_at.isoformat(),
    }


@router.post("/gc-points/adjust")
async def admin_adjust_gc_points(
    body: AdminGCPointsAdjust,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    repo = GamingBookingRepository(db)
    balance = await repo.ensure_gc_points(body.user_id)
    balance.balance += body.amount
    if body.amount > 0:
        balance.lifetime_earned += body.amount
    balance.updated_at = datetime.now(UTC)

    tx_type = "earn" if body.amount >= 0 else "redeem"
    await repo.add_gc_transaction(
        GCPointsTransaction(
            user_id=body.user_id,
            amount=body.amount,
            transaction_type=tx_type,
            description=body.description or "Admin adjustment",
        )
    )
    await db.commit()
    await db.refresh(balance)
    return {
        "user_id": str(balance.user_id),
        "balance": balance.balance,
        "lifetime_earned": balance.lifetime_earned,
        "adjusted_by": str(current_user.id),
    }