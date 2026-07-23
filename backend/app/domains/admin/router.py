"""Admin panel API — full CRUD, moderation, analytics (ADMIN role only)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.admin.schemas import (
    AdminAssignOwner,
    AdminBookingStatusPatch,
    AdminBroadcastRequest,
    AdminOfferUpdate,
    AdminParlorCreate,
    AdminParlorUpdate,
    AdminParlorVerify,
    AdminSlotUpdate,
    AdminTournamentStatus,
    AdminUserPatch,
)
from app.domains.admin.service import AdminService, paginated
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
from app.domains.user.models import User, UserRole
from app.domains.user.schemas import UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


def _require_admin(user) -> None:
    role = user.role.value if hasattr(user.role, "value") else user.role
    if role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


# ── Stats / Analytics ──────────────────────────────────────────────────


@router.get("/stats")
async def admin_stats(current_user: CurrentUserDep, db: DbSessionDep) -> dict:
    _require_admin(current_user)
    return await AdminService(db).stats()


@router.get("/analytics")
async def admin_analytics(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    period: str = "30d",
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).analytics(period)


# ── Users ──────────────────────────────────────────────────────────────


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

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    result = await db.execute(
        query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    users = result.scalars().all()
    items = [UserResponse.model_validate(u).model_dump(mode="json") for u in users]
    return paginated(items, int(total), page, limit)


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
    body: AdminUserPatch,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).update_user(user_id, body)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    """Soft-delete: sets is_active=False (preferred over hard delete)."""
    _require_admin(current_user)
    await AdminService(db).soft_delete_user(user_id, current_user.id)


# ── Parlors ────────────────────────────────────────────────────────────


@router.get("/parlors")
async def admin_list_parlors(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    is_verified: bool | None = None,
    is_active: bool | None = None,
    include_deleted: bool = False,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_parlors(
        page=page,
        limit=limit,
        search=search,
        is_verified=is_verified,
        is_active=is_active,
        include_deleted=include_deleted,
    )


@router.get("/parlors/{parlor_id}")
async def admin_get_parlor(
    parlor_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).get_parlor(parlor_id)


@router.post("/parlors", status_code=status.HTTP_201_CREATED)
async def admin_create_parlor(
    body: AdminParlorCreate,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).create_parlor(body)


@router.patch("/parlors/{parlor_id}")
@router.put("/parlors/{parlor_id}")
async def admin_update_parlor(
    parlor_id: UUID,
    body: AdminParlorUpdate,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).update_parlor(parlor_id, body)


@router.patch("/parlors/{parlor_id}/verify")
async def admin_verify_parlor(
    parlor_id: UUID,
    body: AdminParlorVerify,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).verify_parlor(parlor_id, body.is_verified)


@router.patch("/parlors/{parlor_id}/assign-owner")
async def admin_assign_owner(
    parlor_id: UUID,
    body: AdminAssignOwner,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    """Assign / clear manager (parlor_owner) for a venue."""
    _require_admin(current_user)
    return await AdminService(db).assign_owner(parlor_id, body)


@router.delete("/parlors/{parlor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_parlor(
    parlor_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    """Soft-delete parlor (is_deleted=True, is_active=False)."""
    _require_admin(current_user)
    await AdminService(db).soft_delete_parlor(parlor_id)


@router.post("/parlors/{parlor_id}/restore")
async def admin_restore_parlor(
    parlor_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).restore_parlor(parlor_id)


# ── Posts / Reels / Comments / Likes ───────────────────────────────────


@router.get("/posts")
async def admin_list_posts(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_posts(page, limit, search)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_post(
    post_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).delete_post(post_id)


@router.get("/reels")
async def admin_list_reels(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_reels(page, limit)


@router.delete("/reels/{reel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_reel(
    reel_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).delete_reel(reel_id)


@router.get("/comments")
async def admin_list_comments(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
    is_deleted: bool | None = None,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_comments(page, limit, is_deleted)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_comment(
    comment_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).soft_delete_comment(comment_id)


@router.patch("/comments/{comment_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def admin_restore_comment(
    comment_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).restore_comment(comment_id)


@router.get("/likes")
async def admin_list_likes(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
    target_type: str | None = None,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_likes(page, limit, target_type)


@router.delete("/likes/{like_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_like(
    like_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).delete_like(like_id)


# ── Tournaments / Bookings ─────────────────────────────────────────────


@router.get("/tournaments")
async def admin_list_tournaments(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
    status_filter: str | None = Query(default=None, alias="status"),
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_tournaments(page, limit, status_filter)


@router.patch("/tournaments/{tournament_id}/status")
async def admin_update_tournament_status(
    tournament_id: UUID,
    body: AdminTournamentStatus,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).update_tournament_status(tournament_id, body.status)


@router.delete("/tournaments/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_tournament(
    tournament_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).delete_tournament(tournament_id)


@router.get("/bookings")
async def admin_list_tournament_bookings(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
    user_id: UUID | None = None,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_tournament_bookings(page, limit, user_id)


# ── Gaming bookings (OYO-style) ────────────────────────────────────────


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
    return paginated(
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


@router.patch("/gaming-bookings/{booking_id}")
async def admin_patch_gaming_booking(
    booking_id: UUID,
    body: AdminBookingStatusPatch,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> GamingBookingResponse:
    _require_admin(current_user)
    repo = GamingBookingRepository(db)
    booking = await repo.get_booking_by_id(booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if body.booking_status is not None:
        booking.booking_status = body.booking_status
    if body.payment_status is not None:
        booking.payment_status = body.payment_status
    await db.commit()
    return await GamingBookingService(db).get_booking(booking_id)


@router.patch("/gaming-bookings/{booking_id}/process-refund", response_model=GamingBookingResponse)
async def admin_process_refund(
    booking_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> GamingBookingResponse:
    _require_admin(current_user)
    repo = GamingBookingRepository(db)
    booking = await repo.get_booking_by_id(booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.refund_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking not found or refund not pending",
        )
    booking.refund_status = "processed"
    booking.booking_status = "cancelled"
    await db.commit()
    return await GamingBookingService(db).get_booking(booking_id)


# ── Offers (aliases: /gaming-offers and /offers) ───────────────────────


async def _list_offers(db, parlour_id, page, limit) -> dict:
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
    return paginated(items, int(total), page, limit)


async def _create_offer(db, body: AdminOfferCreate) -> ParlourOfferResponse:
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


@router.get("/gaming-offers")
@router.get("/offers")
async def admin_list_gaming_offers(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    parlour_id: UUID | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    _require_admin(current_user)
    return await _list_offers(db, parlour_id, page, limit)


@router.post("/gaming-offers", response_model=ParlourOfferResponse, status_code=status.HTTP_201_CREATED)
@router.post("/offers", response_model=ParlourOfferResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_gaming_offer(
    body: AdminOfferCreate,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> ParlourOfferResponse:
    _require_admin(current_user)
    return await _create_offer(db, body)


@router.patch("/gaming-offers/{offer_id}")
@router.patch("/offers/{offer_id}")
async def admin_update_offer(
    offer_id: UUID,
    body: AdminOfferUpdate,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).update_offer(offer_id, body.model_dump(exclude_unset=True))


@router.delete("/gaming-offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_offer(
    offer_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).delete_offer(offer_id)


# ── Slots ──────────────────────────────────────────────────────────────


@router.get("/gaming-slots")
@router.get("/slots")
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
    return paginated(items, int(total), page, limit)


@router.post("/gaming-slots", response_model=GamingSlotResponse, status_code=status.HTTP_201_CREATED)
@router.post("/slots", response_model=GamingSlotResponse, status_code=status.HTTP_201_CREATED)
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


@router.patch("/gaming-slots/{slot_id}")
@router.patch("/slots/{slot_id}")
async def admin_update_slot(
    slot_id: UUID,
    body: AdminSlotUpdate,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).update_slot(slot_id, body.model_dump(exclude_unset=True))


@router.delete("/gaming-slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_slot(
    slot_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).delete_slot(slot_id)


# ── GC Points ──────────────────────────────────────────────────────────


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


# ── Ratings / Geo / Broadcast ──────────────────────────────────────────


@router.get("/ratings")
async def admin_list_ratings(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_ratings(page, limit)


@router.delete("/ratings/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_rating(
    rating_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).delete_rating(rating_id)


@router.get("/geo-activity")
async def admin_geo_activity(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_geo_activity(page, limit)


@router.post("/notifications/broadcast")
async def admin_broadcast(
    body: AdminBroadcastRequest,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).broadcast(
        body.title, body.body, body.target, body.type, current_user.id
    )


@router.get("/notifications/history")
async def admin_broadcast_history(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """No dedicated broadcast log table — return empty paginated list."""
    _require_admin(current_user)
    return paginated([], 0, max(1, page), min(max(1, limit), 100))


@router.get("/stories")
async def admin_list_stories(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
) -> dict:
    _require_admin(current_user)
    return await AdminService(db).list_stories(page, limit)


@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_story(
    story_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
) -> None:
    _require_admin(current_user)
    await AdminService(db).delete_story(story_id)


@router.get("/events")
async def admin_list_events(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Events feature not yet backed by a dedicated table — empty list."""
    _require_admin(current_user)
    return paginated([], 0, max(1, page), min(max(1, limit), 100))


@router.get("/community")
async def admin_list_community(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Community board not yet backed — empty list (Flutter communities is UI-only)."""
    _require_admin(current_user)
    return paginated([], 0, max(1, page), min(max(1, limit), 100))
