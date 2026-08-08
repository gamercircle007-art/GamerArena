"""Club Management — platform admin oversight.

Read-only visibility into any club, plus a small set of override controls. Deliberately
NOT the owner workflow: an admin can force-cancel, disable or flag, but does not create
resources, price rules or walk-ins on an owner's behalf.

Admin identity is checked once here (`_require_admin`) rather than reusing the owner
router's `ClubScope.resolve_club_id`, because that method requires ownership; admins
own nothing and must be able to inspect every club.

The override flags (`ClubPromotion.disabled_by_platform`, `ClubCustomer.platform_flagged`)
are separate columns from the owner-controlled ones on purpose — an owner toggling
`is_active` back on must not silently undo a platform decision.
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.club_ops.analytics_service import OccupancyService, RevenueService
from app.domains.club_ops.enums import RollupGrain
from app.domains.club_ops.models import ClubCustomer, ClubPromotion, ClubResource, ClubZone
from app.domains.club_ops.repository import is_platform_admin
from app.domains.club_ops.schemas import (
    AdminCustomerFlagRequest,
    AdminForceCancelRequest,
    AdminPromotionDisableRequest,
    AdminResourceDeactivateRequest,
)
from app.domains.club_ops.service import CustomerService, OwnerBookingService, today_ist
from app.domains.common.exceptions import ForbiddenError, NotFoundError
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension

router = APIRouter(prefix="/admin/club-management", tags=["Admin — Club Management"])


def _require_admin(user) -> None:
    if not is_platform_admin(user):
        raise ForbiddenError("Platform admin only")


def _window(from_date: date_cls | None, to_date: date_cls | None) -> tuple[date_cls, date_cls]:
    end = to_date or today_ist()
    start = from_date or (end - timedelta(days=29))
    return start, end


@router.get("/clubs")
async def list_clubs(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """Clubs that have any Club Management data configured, for the admin picker."""
    _require_admin(current_user)
    stmt = (
        select(GamingPlace.id, GamingPlace.name, GamingPlaceExtension.owner_id)
        .outerjoin(
            GamingPlaceExtension, GamingPlaceExtension.gaming_place_id == GamingPlace.id
        )
        .where(GamingPlaceExtension.is_deleted.is_(False))
    )
    if search:
        stmt = stmt.where(GamingPlace.name.ilike(f"%{search.strip()}%"))
    rows = (await db.execute(stmt.order_by(GamingPlace.name.asc()).limit(limit).offset(offset))).all()
    return {
        "items": [
            {"parlor_id": str(pid), "name": name, "owner_id": str(oid) if oid else None}
            for pid, name, oid in rows
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/clubs/{parlor_id}/resources")
async def admin_list_resources(
    parlor_id: UUID, db: DbSessionDep, current_user: CurrentUserDep
) -> dict:
    """Read-only view of a club's floor."""
    _require_admin(current_user)
    rows = (
        await db.execute(
            select(ClubResource, ClubZone.name)
            .outerjoin(ClubZone, ClubResource.zone_id == ClubZone.id)
            .where(ClubResource.parlor_id == parlor_id)
            .order_by(ClubResource.label.asc())
        )
    ).all()
    return {
        "parlor_id": str(parlor_id),
        "items": [
            {
                "id": str(resource.id),
                "label": resource.label,
                "resource_type": resource.resource_type,
                "status": resource.status,
                "zone_name": zone_name,
                "zone_id": str(resource.zone_id) if resource.zone_id else None,
                "hourly_rate_override_paise": resource.hourly_rate_override_paise,
                "layout_x": resource.layout_x,
                "layout_y": resource.layout_y,
                "is_active": resource.is_active,
                "status_note": resource.status_note,
            }
            for resource, zone_name in rows
        ],
    }


@router.get("/clubs/{parlor_id}/live")
async def admin_live(parlor_id: UUID, db: DbSessionDep, current_user: CurrentUserDep) -> dict:
    _require_admin(current_user)
    rows = await OwnerBookingService(db).live_now(parlor_id)
    return {
        "parlor_id": str(parlor_id),
        "occupants": [
            {
                **row,
                "booking_id": str(row["booking_id"]),
                "resource_id": str(row["resource_id"]) if row["resource_id"] else None,
            }
            for row in rows
        ],
    }


@router.get("/clubs/{parlor_id}/revenue")
async def admin_revenue(
    parlor_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    range: str = Query("month", pattern="^(today|week|month)$"),
) -> dict:
    _require_admin(current_user)
    data = await RevenueService(db).summary(parlor_id, range_key=range)
    data["from_date"] = data["from_date"].isoformat()
    data["to_date"] = data["to_date"].isoformat()
    return data


@router.get("/clubs/{parlor_id}/occupancy")
async def admin_occupancy(
    parlor_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    from_date: date_cls | None = None,
    to_date: date_cls | None = None,
) -> dict:
    """Heatmap + utilisation + no-show in one call — the admin view shows all three."""
    _require_admin(current_user)
    start, end = _window(from_date, to_date)
    service = OccupancyService(db)
    return {
        "parlor_id": str(parlor_id),
        "from_date": start.isoformat(),
        "to_date": end.isoformat(),
        "heatmap": await service.heatmap(parlor_id, from_date=start, to_date=end),
        "utilization": await service.utilization(
            parlor_id, from_date=start, to_date=end, grain=RollupGrain.RESOURCE.value
        ),
        "no_show": await service.no_show_rate(parlor_id, from_date=start, to_date=end),
    }


@router.get("/clubs/{parlor_id}/bookings")
async def admin_list_bookings(
    parlor_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    date: date_cls | None = None,
    view: str = Query("day", pattern="^(day|week)$"),
) -> dict:
    _require_admin(current_user)
    bookings = await OwnerBookingService(db).list_bookings(
        parlor_id, target_date=date, view=view
    )
    return {
        "parlor_id": str(parlor_id),
        "items": [
            {
                "id": str(b.id),
                "booking_ref": b.booking_ref,
                "slot_date": b.slot_date.isoformat() if b.slot_date else None,
                "start_time": b.start_time.isoformat() if b.start_time else None,
                "booking_status": b.booking_status,
                "payment_status": b.payment_status,
                "amount_paise": b.amount_paise,
                "commission_paise": b.commission_paise,
                "is_walk_in": b.is_walk_in,
                "station_type": b.station_type,
                "guest_name": b.guest_name,
                "contact_phone": b.contact_phone,
            }
            for b in bookings
        ],
    }


@router.get("/clubs/{parlor_id}/promotions")
async def admin_list_promotions(
    parlor_id: UUID, db: DbSessionDep, current_user: CurrentUserDep
) -> dict:
    _require_admin(current_user)
    rows = (
        await db.execute(
            select(ClubPromotion)
            .where(ClubPromotion.parlor_id == parlor_id)
            .order_by(ClubPromotion.created_at.desc())
        )
    ).scalars().all()
    return {
        "parlor_id": str(parlor_id),
        "items": [
            {
                "id": str(p.id),
                "name": p.name,
                "promo_type": p.promo_type,
                "percent_bps": p.percent_bps,
                "flat_paise": p.flat_paise,
                "code": p.code,
                "used_count": p.used_count,
                "usage_limit": p.usage_limit,
                "is_active": p.is_active,
                "disabled_by_platform": p.disabled_by_platform,
                "disabled_reason": p.disabled_reason,
                "valid_from": p.valid_from.isoformat() if p.valid_from else None,
                "valid_to": p.valid_to.isoformat() if p.valid_to else None,
            }
            for p in rows
        ],
    }


@router.get("/clubs/{parlor_id}/customers")
async def admin_list_customers(
    parlor_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    _require_admin(current_user)
    service = CustomerService(db)
    customers, total = await service.list_customers(
        parlor_id, search=search, limit=limit, offset=offset
    )
    items = []
    for customer in customers:
        items.append(
            {
                "id": str(customer.id),
                "display_name": await service.resolve_name(customer),
                "phone": customer.phone,
                "user_id": str(customer.user_id) if customer.user_id else None,
                "visit_count": customer.visit_count,
                "total_spend_paise": customer.total_spend_paise,
                "loyalty_points": customer.loyalty_points,
                "is_banned": customer.is_banned,
                "ban_reason": customer.ban_reason,
                "platform_flagged": customer.platform_flagged,
                "platform_flag_reason": customer.platform_flag_reason,
                "last_visit_at": customer.last_visit_at.isoformat()
                if customer.last_visit_at
                else None,
            }
        )
    return {"parlor_id": str(parlor_id), "items": items, "total": total}


# --- Override controls ------------------------------------------------------------


@router.post("/clubs/{parlor_id}/bookings/{booking_id}/force-cancel")
async def force_cancel_booking(
    parlor_id: UUID,
    booking_id: UUID,
    body: AdminForceCancelRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    """Cancel a booking regardless of the owner's cancellation window."""
    _require_admin(current_user)
    booking = await OwnerBookingService(db).cancel(
        parlor_id,
        booking_id,
        reason=body.reason,
        detail=body.detail,
        actor_id=current_user.id,
        actor="admin",
    )
    return {
        "id": str(booking.id),
        "booking_status": booking.booking_status,
        "cancelled_by": booking.cancelled_by,
        "cancellation_reason": booking.cancellation_reason,
    }


@router.post("/clubs/{parlor_id}/promotions/{promotion_id}/disable")
async def disable_promotion(
    parlor_id: UUID,
    promotion_id: UUID,
    body: AdminPromotionDisableRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    _require_admin(current_user)
    promo = (
        await db.execute(
            select(ClubPromotion).where(
                ClubPromotion.id == promotion_id, ClubPromotion.parlor_id == parlor_id
            )
        )
    ).scalar_one_or_none()
    if promo is None:
        raise NotFoundError("Promotion not found")
    promo.disabled_by_platform = body.disabled
    promo.disabled_reason = body.reason if body.disabled else None
    await db.commit()
    return {
        "id": str(promo.id),
        "disabled_by_platform": promo.disabled_by_platform,
        "disabled_reason": promo.disabled_reason,
    }


@router.post("/clubs/{parlor_id}/resources/{resource_id}/deactivate")
async def deactivate_resource(
    parlor_id: UUID,
    resource_id: UUID,
    body: AdminResourceDeactivateRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    _require_admin(current_user)
    resource = (
        await db.execute(
            select(ClubResource).where(
                ClubResource.id == resource_id, ClubResource.parlor_id == parlor_id
            )
        )
    ).scalar_one_or_none()
    if resource is None:
        raise NotFoundError("Resource not found")
    resource.is_active = body.is_active
    if not body.is_active:
        resource.status = "offline"
    resource.status_note = body.reason
    await db.commit()
    return {
        "id": str(resource.id),
        "is_active": resource.is_active,
        "status": resource.status,
        "status_note": resource.status_note,
    }


@router.post("/clubs/{parlor_id}/customers/{customer_id}/flag")
async def flag_customer(
    parlor_id: UUID,
    customer_id: UUID,
    body: AdminCustomerFlagRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    """Platform-level flag/ban. Independent of the club's own `is_banned`."""
    _require_admin(current_user)
    customer = (
        await db.execute(
            select(ClubCustomer).where(
                ClubCustomer.id == customer_id, ClubCustomer.parlor_id == parlor_id
            )
        )
    ).scalar_one_or_none()
    if customer is None:
        raise NotFoundError("Customer not found")
    customer.platform_flagged = body.flagged
    customer.platform_flag_reason = body.reason if body.flagged else None
    await db.commit()
    return {
        "id": str(customer.id),
        "platform_flagged": customer.platform_flagged,
        "platform_flag_reason": customer.platform_flag_reason,
    }
