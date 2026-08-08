"""Club Management API — owner-facing.

Every endpoint resolves its club through `ClubScope.resolve_club_id` as its first act.
`parlor_id` is an optional query parameter: an owner may omit it (their single club is
inferred), a platform admin must supply it. A cross-club id yields 403, which Phase 5
asserts explicitly.
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
from app.domains.club_ops.models import ClubCustomer, ClubResource
from app.domains.club_ops.pricing import PriceResolver
from app.domains.club_ops.promotions import PromotionService, assert_promo_value
from app.domains.club_ops.repository import ClubScope
from app.domains.club_ops.schemas import (
    BulkResourceStatusUpdate,
    CancelBookingRequest,
    CustomerBanRequest,
    CustomerDetailResponse,
    CustomerNoteRequest,
    CustomerNoteResponse,
    CustomerResponse,
    CustomerTagRequest,
    ExtendBookingRequest,
    FloorLayoutUpdate,
    LiveOccupantResponse,
    NoShowRateResponse,
    OwnerBookingResponse,
    PricePreviewRequest,
    PricePreviewResponse,
    PricingRuleCreate,
    PricingRuleResponse,
    PricingRuleUpdate,
    PromotionCreate,
    PromotionResponse,
    PromotionUpdate,
    PromotionValidateRequest,
    ResourceCreate,
    ResourceResponse,
    ResourceStatusUpdate,
    ResourceUpdate,
    RevenueSummaryResponse,
    WalkInBookingRequest,
    ZoneCreate,
    ZoneResponse,
    ZoneUpdate,
)
from app.domains.club_ops.service import (
    CustomerService,
    OwnerBookingService,
    PricingRuleService,
    ResourceService,
    ZoneService,
    today_ist,
)
from app.domains.club_ops.models import ClubPromotion

router = APIRouter(prefix="/club", tags=["Club Management"])

ParlorIdQuery = Query(
    None,
    description="Club to act on. Owners may omit it; platform admins must supply it.",
)


# --- serialisation helpers ---------------------------------------------------------


def _resource_out(resource: ClubResource, zone_name: str | None = None) -> ResourceResponse:
    return ResourceResponse(
        id=resource.id,
        parlor_id=resource.parlor_id,
        zone_id=resource.zone_id,
        zone_name=zone_name,
        resource_type=resource.resource_type,
        label=resource.label,
        status=resource.status,
        specs=resource.specs,
        hourly_rate_override_paise=resource.hourly_rate_override_paise,
        layout_x=resource.layout_x,
        layout_y=resource.layout_y,
        status_note=resource.status_note,
        is_active=resource.is_active,
    )


def _customer_out(customer: ClubCustomer, name: str | None = None) -> CustomerResponse:
    return CustomerResponse(
        id=customer.id,
        parlor_id=customer.parlor_id,
        user_id=customer.user_id,
        display_name=name or customer.display_name,
        phone=customer.phone,
        visit_count=customer.visit_count,
        total_spend_paise=customer.total_spend_paise,
        total_spend_rupees=f"{customer.total_spend_paise / 100:.2f}",
        last_visit_at=customer.last_visit_at,
        loyalty_points=customer.loyalty_points,
        tags=customer.tags,
        notes=customer.notes,
        is_banned=customer.is_banned,
        ban_reason=customer.ban_reason,
        platform_flagged=customer.platform_flagged,
    )


async def _booking_out(db, booking) -> OwnerBookingResponse:
    resource_label = None
    if booking.resource_id is not None:
        resource_label = (
            await db.execute(
                select(ClubResource.label).where(ClubResource.id == booking.resource_id)
            )
        ).scalar_one_or_none()

    customer_name = booking.guest_name
    if not customer_name and booking.club_customer_id is not None:
        customer = (
            await db.execute(
                select(ClubCustomer).where(ClubCustomer.id == booking.club_customer_id)
            )
        ).scalar_one_or_none()
        if customer is not None:
            customer_name = await CustomerService(db).resolve_name(customer)

    return OwnerBookingResponse(
        id=booking.id,
        booking_ref=booking.booking_ref,
        parlour_id=booking.parlour_id,
        user_id=booking.user_id,
        resource_id=booking.resource_id,
        resource_label=resource_label,
        club_customer_id=booking.club_customer_id,
        customer_name=customer_name,
        contact_phone=booking.contact_phone,
        station_type=booking.station_type,
        slot_date=booking.slot_date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        duration_hours=booking.duration_hours,
        units=booking.units,
        booking_status=booking.booking_status,
        payment_status=booking.payment_status,
        payment_mode=booking.payment_mode,
        amount_paise=booking.amount_paise,
        club_discount_paise=booking.club_discount_paise or 0,
        commission_paise=booking.commission_paise,
        is_walk_in=booking.is_walk_in,
        checked_in_at=booking.checked_in_at,
        checked_out_at=booking.checked_out_at,
        extended_hours=booking.extended_hours or 0,
        no_show_at=booking.no_show_at,
        cancellation_reason=booking.cancellation_reason,
        created_at=booking.created_at,
    )


# --- Seat / PC management: zones ---------------------------------------------------


@router.get("/zones", response_model=list[ZoneResponse])
async def list_zones(
    db: DbSessionDep, current_user: CurrentUserDep, parlor_id: UUID | None = ParlorIdQuery
) -> list[ZoneResponse]:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    return [
        ZoneResponse(
            id=zone.id,
            parlor_id=zone.parlor_id,
            name=zone.name,
            description=zone.description,
            sort_order=zone.sort_order,
            is_active=zone.is_active,
            resource_count=count,
        )
        for zone, count in await ZoneService(db).list_zones(club_id)
    ]


@router.post("/zones", response_model=ZoneResponse, status_code=201)
async def create_zone(
    body: ZoneCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> ZoneResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    zone = await ZoneService(db).create(club_id, body)
    return ZoneResponse.model_validate(zone)


@router.patch("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: UUID,
    body: ZoneUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> ZoneResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    zone = await ZoneService(db).update(club_id, zone_id, body)
    return ZoneResponse.model_validate(zone)


@router.delete("/zones/{zone_id}", status_code=204)
async def delete_zone(
    zone_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> None:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    await ZoneService(db).delete(club_id, zone_id)


# --- Seat / PC management: resources ----------------------------------------------


@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    zone_id: UUID | None = None,
    resource_type: str | None = None,
    status: str | None = None,
    include_inactive: bool = False,
) -> list[ResourceResponse]:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    rows = await ResourceService(db).list_resources(
        club_id,
        zone_id=zone_id,
        resource_type=resource_type,
        status=status,
        include_inactive=include_inactive,
    )
    return [_resource_out(resource, zone_name) for resource, zone_name in rows]


@router.post("/resources", response_model=ResourceResponse, status_code=201)
async def create_resource(
    body: ResourceCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> ResourceResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    resource = await ResourceService(db).create(club_id, body)
    return _resource_out(resource)


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> ResourceResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    resource = await ResourceService(db).get(club_id, resource_id)
    return _resource_out(resource)


@router.patch("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: UUID,
    body: ResourceUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> ResourceResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    resource = await ResourceService(db).update(club_id, resource_id, body)
    return _resource_out(resource)


@router.delete("/resources/{resource_id}", status_code=204)
async def delete_resource(
    resource_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> None:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    await ResourceService(db).delete(club_id, resource_id)


@router.patch("/resources/{resource_id}/status", response_model=ResourceResponse)
async def set_resource_status(
    resource_id: UUID,
    body: ResourceStatusUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> ResourceResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    resource = await ResourceService(db).set_status(
        club_id, resource_id, body.status.value, body.status_note
    )
    return _resource_out(resource)


@router.post("/resources/status/bulk")
async def bulk_set_resource_status(
    body: BulkResourceStatusUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> dict:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    updated = await ResourceService(db).bulk_set_status(
        club_id, body.resource_ids, body.status.value, body.status_note
    )
    return {"updated": updated, "status": body.status.value}


@router.put("/floor-layout")
async def save_floor_layout(
    body: FloorLayoutUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> dict:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    saved = await ResourceService(db).save_layout(club_id, body.positions)
    return {"saved": saved}


# --- Booking management (owner side) ----------------------------------------------


@router.get("/bookings", response_model=list[OwnerBookingResponse])
async def list_bookings(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    date: date_cls | None = None,
    view: str = Query("day", pattern="^(day|week)$"),
    status: str | None = None,
) -> list[OwnerBookingResponse]:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    bookings = await OwnerBookingService(db).list_bookings(
        club_id, target_date=date, view=view, status=status
    )
    return [await _booking_out(db, booking) for booking in bookings]


@router.post("/bookings/walk-in", response_model=OwnerBookingResponse, status_code=201)
async def create_walk_in(
    body: WalkInBookingRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> OwnerBookingResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    booking = await OwnerBookingService(db).create_walk_in(
        club_id, body, actor_id=current_user.id
    )
    return await _booking_out(db, booking)


@router.post("/bookings/{booking_id}/confirm", response_model=OwnerBookingResponse)
async def confirm_booking(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> OwnerBookingResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    booking = await OwnerBookingService(db).confirm(club_id, booking_id, current_user.id)
    return await _booking_out(db, booking)


@router.post("/bookings/{booking_id}/cancel", response_model=OwnerBookingResponse)
async def cancel_booking(
    booking_id: UUID,
    body: CancelBookingRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> OwnerBookingResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    booking = await OwnerBookingService(db).cancel(
        club_id,
        booking_id,
        reason=body.reason,
        detail=body.detail,
        actor_id=current_user.id,
    )
    return await _booking_out(db, booking)


@router.post("/bookings/{booking_id}/check-in", response_model=OwnerBookingResponse)
async def check_in_booking(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> OwnerBookingResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    booking = await OwnerBookingService(db).check_in(club_id, booking_id, current_user.id)
    return await _booking_out(db, booking)


@router.post("/bookings/{booking_id}/check-out", response_model=OwnerBookingResponse)
async def check_out_booking(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> OwnerBookingResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    booking = await OwnerBookingService(db).check_out(club_id, booking_id, current_user.id)
    return await _booking_out(db, booking)


@router.post("/bookings/{booking_id}/extend", response_model=OwnerBookingResponse)
async def extend_booking(
    booking_id: UUID,
    body: ExtendBookingRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> OwnerBookingResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    booking = await OwnerBookingService(db).extend(
        club_id, booking_id, body.additional_hours, current_user.id
    )
    return await _booking_out(db, booking)


@router.post("/bookings/{booking_id}/no-show", response_model=OwnerBookingResponse)
async def mark_no_show(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> OwnerBookingResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    booking = await OwnerBookingService(db).mark_no_show(club_id, booking_id, current_user.id)
    return await _booking_out(db, booking)


@router.get("/live", response_model=list[LiveOccupantResponse])
async def live_now(
    db: DbSessionDep, current_user: CurrentUserDep, parlor_id: UUID | None = ParlorIdQuery
) -> list[LiveOccupantResponse]:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    rows = await OwnerBookingService(db).live_now(club_id)
    return [LiveOccupantResponse(**row) for row in rows]


# --- Customer management ----------------------------------------------------------


@router.get("/customers")
async def list_customers(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    service = CustomerService(db)
    customers, total = await service.list_customers(
        club_id, search=search, limit=limit, offset=offset
    )
    items = []
    for customer in customers:
        items.append(_customer_out(customer, await service.resolve_name(customer)))
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> CustomerDetailResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    service = CustomerService(db)
    customer = await service.get(club_id, customer_id)
    bookings = await OwnerBookingService(db).recent_for_customer(club_id, customer_id)
    notes = await service.list_notes(club_id, customer_id)
    return CustomerDetailResponse(
        customer=_customer_out(customer, await service.resolve_name(customer)),
        recent_bookings=[await _booking_out(db, booking) for booking in bookings],
        note_history=[CustomerNoteResponse.model_validate(note) for note in notes],
    )


@router.post("/customers/{customer_id}/note", response_model=CustomerNoteResponse, status_code=201)
async def add_customer_note(
    customer_id: UUID,
    body: CustomerNoteRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> CustomerNoteResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    note = await CustomerService(db).add_note(
        club_id, customer_id, body.body, current_user.id
    )
    return CustomerNoteResponse.model_validate(note)


@router.post("/customers/{customer_id}/tags", response_model=CustomerResponse)
async def set_customer_tags(
    customer_id: UUID,
    body: CustomerTagRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> CustomerResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    service = CustomerService(db)
    customer = await service.set_tags(club_id, customer_id, body.tags)
    return _customer_out(customer, await service.resolve_name(customer))


@router.post("/customers/{customer_id}/ban", response_model=CustomerResponse)
async def ban_customer(
    customer_id: UUID,
    body: CustomerBanRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> CustomerResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    service = CustomerService(db)
    customer = await service.set_ban(
        club_id, customer_id, banned=body.is_banned, reason=body.reason
    )
    return _customer_out(customer, await service.resolve_name(customer))


# --- Pricing control -------------------------------------------------------------


@router.get("/pricing/rules", response_model=list[PricingRuleResponse])
async def list_pricing_rules(
    db: DbSessionDep, current_user: CurrentUserDep, parlor_id: UUID | None = ParlorIdQuery
) -> list[PricingRuleResponse]:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    rules = await PricingRuleService(db).list_rules(club_id)
    return [PricingRuleResponse.model_validate(rule) for rule in rules]


@router.post("/pricing/rules", response_model=PricingRuleResponse, status_code=201)
async def create_pricing_rule(
    body: PricingRuleCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> PricingRuleResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    rule = await PricingRuleService(db).create(club_id, body)
    return PricingRuleResponse.model_validate(rule)


@router.get("/pricing/rules/{rule_id}", response_model=PricingRuleResponse)
async def get_pricing_rule(
    rule_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> PricingRuleResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    rule = await PricingRuleService(db).get(club_id, rule_id)
    return PricingRuleResponse.model_validate(rule)


@router.patch("/pricing/rules/{rule_id}", response_model=PricingRuleResponse)
async def update_pricing_rule(
    rule_id: UUID,
    body: PricingRuleUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> PricingRuleResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    rule = await PricingRuleService(db).update(club_id, rule_id, body)
    return PricingRuleResponse.model_validate(rule)


@router.delete("/pricing/rules/{rule_id}", status_code=204)
async def delete_pricing_rule(
    rule_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> None:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    await PricingRuleService(db).delete(club_id, rule_id)


@router.post("/pricing/preview", response_model=PricePreviewResponse)
async def preview_price(
    body: PricePreviewRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> PricePreviewResponse:
    """Price a hypothetical booking, showing which rule and slab applied.

    Calls the same `PriceResolver` the booking paths use, so the preview cannot drift
    from what the customer is actually charged.
    """
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    breakdown = await PriceResolver(db).resolve(
        parlor_id=club_id,
        resource_type=body.resource_type.value,
        booking_date=body.booking_date,
        start_time=body.start_time,
        duration_hours=body.duration_hours,
        units=body.units,
        resource_id=body.resource_id,
        zone_id=body.zone_id,
    )
    promo = await PromotionService(db).apply_best(
        parlor_id=club_id,
        subtotal_paise=breakdown.subtotal_paise,
        resource_type=body.resource_type.value,
        booking_date=body.booking_date,
        start_time=body.start_time,
        code=body.promo_code,
        club_customer_id=body.club_customer_id,
    )
    discount = promo.discount_paise if promo.valid else 0
    total = max(0, breakdown.subtotal_paise - discount)
    return PricePreviewResponse(
        breakdown=breakdown.as_dict(),
        promotion=promo.as_dict(),
        subtotal_paise=breakdown.subtotal_paise,
        discount_paise=discount,
        total_paise=total,
        total_rupees=f"{total / 100:.2f}",
    )


# --- Promotions ------------------------------------------------------------------


@router.get("/promotions", response_model=list[PromotionResponse])
async def list_promotions(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    active_only: bool = False,
) -> list[PromotionResponse]:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    promos = await PromotionService(db).list_for_club(club_id, active_only=active_only)
    return [PromotionResponse.model_validate(promo) for promo in promos]


@router.post("/promotions", response_model=PromotionResponse, status_code=201)
async def create_promotion(
    body: PromotionCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> PromotionResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    assert_promo_value(body.percent_bps, body.flat_paise)
    promo = ClubPromotion(
        parlor_id=club_id,
        name=body.name.strip(),
        promo_type=body.promo_type.value,
        percent_bps=body.percent_bps,
        flat_paise=body.flat_paise,
        code=body.code.strip().upper() if body.code else None,
        max_discount_paise=body.max_discount_paise,
        min_amount_paise=body.min_amount_paise,
        valid_from=body.valid_from,
        valid_to=body.valid_to,
        happy_hour_start=body.happy_hour_start,
        happy_hour_end=body.happy_hour_end,
        usage_limit=body.usage_limit,
        used_count=0,
        applicable_resource_types=[t.value for t in body.applicable_resource_types]
        if body.applicable_resource_types
        else None,
        min_loyalty_points=body.min_loyalty_points,
        is_active=body.is_active,
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return PromotionResponse.model_validate(promo)


@router.get("/promotions/{promotion_id}", response_model=PromotionResponse)
async def get_promotion(
    promotion_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> PromotionResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    promo = await PromotionService(db).get_scoped(club_id, promotion_id)
    return PromotionResponse.model_validate(promo)


@router.patch("/promotions/{promotion_id}", response_model=PromotionResponse)
async def update_promotion(
    promotion_id: UUID,
    body: PromotionUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> PromotionResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    service = PromotionService(db)
    promo = await service.get_scoped(club_id, promotion_id)

    percent = body.percent_bps if body.percent_bps is not None else promo.percent_bps
    flat = body.flat_paise if body.flat_paise is not None else promo.flat_paise
    assert_promo_value(percent, flat)
    promo.percent_bps = percent
    promo.flat_paise = flat

    if body.name is not None:
        promo.name = body.name.strip()
    if body.promo_type is not None:
        promo.promo_type = body.promo_type.value
    if body.code is not None:
        promo.code = body.code.strip().upper() or None
    if body.applicable_resource_types is not None:
        promo.applicable_resource_types = [t.value for t in body.applicable_resource_types]
    for field in (
        "max_discount_paise",
        "min_amount_paise",
        "valid_from",
        "valid_to",
        "happy_hour_start",
        "happy_hour_end",
        "usage_limit",
        "min_loyalty_points",
        "is_active",
    ):
        value = getattr(body, field, None)
        if value is not None:
            setattr(promo, field, value)
    await db.commit()
    await db.refresh(promo)
    return PromotionResponse.model_validate(promo)


@router.delete("/promotions/{promotion_id}", status_code=204)
async def delete_promotion(
    promotion_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> None:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    promo = await PromotionService(db).get_scoped(club_id, promotion_id)
    promo.is_active = False
    await db.commit()


@router.post("/promotions/validate")
async def validate_promotion(
    body: PromotionValidateRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
) -> dict:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    outcome = await PromotionService(db).validate(
        parlor_id=club_id,
        subtotal_paise=body.subtotal_paise,
        resource_type=body.resource_type.value,
        booking_date=body.booking_date,
        start_time=body.start_time,
        code=body.code,
        promotion_id=body.promotion_id,
        club_customer_id=body.club_customer_id,
    )
    return outcome.as_dict()


# --- Revenue ---------------------------------------------------------------------


@router.get("/revenue/summary", response_model=RevenueSummaryResponse)
async def revenue_summary(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    range: str = Query("today", pattern="^(today|week|month)$"),
) -> RevenueSummaryResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    data = await RevenueService(db).summary(club_id, range_key=range)
    return RevenueSummaryResponse(**data)


# --- Occupancy analytics (rollups only) ------------------------------------------


def _default_window(
    from_date: date_cls | None, to_date: date_cls | None
) -> tuple[date_cls, date_cls]:
    """Default the analytics window to the trailing 30 days (IST)."""
    end = to_date or today_ist()
    start = from_date or (end - timedelta(days=29))
    return start, end


@router.get("/occupancy/timeseries")
async def occupancy_timeseries(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    from_date: date_cls | None = None,
    to_date: date_cls | None = None,
    grain: str = Query(RollupGrain.CLUB.value, pattern="^(club|resource_type|zone|resource)$"),
    grain_key: str = "",
) -> dict:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    start, end = _default_window(from_date, to_date)
    points = await OccupancyService(db).timeseries(
        club_id, from_date=start, to_date=end, grain=grain, grain_key=grain_key
    )
    return {"from_date": start, "to_date": end, "grain": grain, "points": points}


@router.get("/occupancy/heatmap")
async def occupancy_heatmap(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    from_date: date_cls | None = None,
    to_date: date_cls | None = None,
) -> dict:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    start, end = _default_window(from_date, to_date)
    cells = await OccupancyService(db).heatmap(club_id, from_date=start, to_date=end)
    return {"from_date": start, "to_date": end, "cells": cells}


@router.get("/occupancy/utilization")
async def occupancy_utilization(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    from_date: date_cls | None = None,
    to_date: date_cls | None = None,
    grain: str = Query(
        RollupGrain.RESOURCE.value, pattern="^(resource_type|zone|resource)$"
    ),
) -> dict:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    start, end = _default_window(from_date, to_date)
    rows = await OccupancyService(db).utilization(
        club_id, from_date=start, to_date=end, grain=grain
    )
    return {"from_date": start, "to_date": end, "grain": grain, "rows": rows}


@router.get("/occupancy/no-show-rate", response_model=NoShowRateResponse)
async def occupancy_no_show_rate(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    parlor_id: UUID | None = ParlorIdQuery,
    from_date: date_cls | None = None,
    to_date: date_cls | None = None,
) -> NoShowRateResponse:
    club_id = await ClubScope(db).resolve_club_id(current_user, parlor_id)
    start, end = _default_window(from_date, to_date)
    data = await OccupancyService(db).no_show_rate(club_id, from_date=start, to_date=end)
    return NoShowRateResponse(**data)
