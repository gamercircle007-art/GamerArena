"""Club Management Pydantic schemas.

Money crosses the wire as integer paise (`*_paise`); responses additionally carry a
formatted `*_rupees` string so clients never do currency arithmetic in floating point.
"""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.club_ops.enums import (
    PricingScope,
    PromotionType,
    ResourceStatus,
    ResourceType,
)

# --- Zones ---


class ZoneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: str | None = None
    sort_order: int = 0


class ZoneUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parlor_id: UUID
    name: str
    description: str | None = None
    sort_order: int
    is_active: bool
    resource_count: int = 0


# --- Resources ---


class ResourceCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=60)
    resource_type: ResourceType = ResourceType.PC
    zone_id: UUID | None = None
    status: ResourceStatus = ResourceStatus.AVAILABLE
    specs: dict | None = None
    hourly_rate_override_paise: int | None = Field(None, ge=0)
    layout_x: int | None = None
    layout_y: int | None = None
    is_active: bool = True


class ResourceUpdate(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=60)
    resource_type: ResourceType | None = None
    zone_id: UUID | None = None
    status: ResourceStatus | None = None
    specs: dict | None = None
    hourly_rate_override_paise: int | None = Field(None, ge=0)
    layout_x: int | None = None
    layout_y: int | None = None
    status_note: str | None = None
    is_active: bool | None = None


class ResourceStatusUpdate(BaseModel):
    status: ResourceStatus
    status_note: str | None = None


class BulkResourceStatusUpdate(BaseModel):
    resource_ids: list[UUID] = Field(..., min_length=1, max_length=200)
    status: ResourceStatus
    status_note: str | None = None


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parlor_id: UUID
    zone_id: UUID | None = None
    zone_name: str | None = None
    resource_type: str
    label: str
    status: str
    specs: dict | None = None
    hourly_rate_override_paise: int | None = None
    layout_x: int | None = None
    layout_y: int | None = None
    status_note: str | None = None
    is_active: bool


class FloorLayoutItem(BaseModel):
    resource_id: UUID
    layout_x: int
    layout_y: int


class FloorLayoutUpdate(BaseModel):
    positions: list[FloorLayoutItem] = Field(..., min_length=1, max_length=500)


# --- Pricing ---


class TimeSlab(BaseModel):
    """A peak/off-peak window. `flat_paise` replaces the hour; `multiplier_bps` scales it."""

    label: str = Field(..., max_length=40)
    start: str = Field(..., description="HH:MM, IST")
    end: str = Field(..., description="HH:MM, IST. May wrap past midnight.")
    multiplier_bps: int | None = Field(None, gt=0, le=100000)
    flat_paise: int | None = Field(None, ge=0)

    @field_validator("start", "end")
    @classmethod
    def _valid_hhmm(cls, value: str) -> str:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("must be HH:MM")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("must be a valid 24h time")
        return f"{hour:02d}:{minute:02d}"


class PackageDef(BaseModel):
    label: str = Field(..., max_length=40)
    hours: int = Field(..., ge=1, le=24)
    price_paise: int = Field(..., ge=0)


class PricingRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    scope: PricingScope = PricingScope.CLUB
    scope_value: str = Field("", max_length=64)
    base_rate_paise: int = Field(..., ge=0)
    time_slabs: list[TimeSlab] | None = None
    day_of_week_overrides: dict[str, dict] | None = None
    package_defs: list[PackageDef] | None = None
    priority: int = 0
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool = True


class PricingRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    scope: PricingScope | None = None
    scope_value: str | None = Field(None, max_length=64)
    base_rate_paise: int | None = Field(None, ge=0)
    time_slabs: list[TimeSlab] | None = None
    day_of_week_overrides: dict[str, dict] | None = None
    package_defs: list[PackageDef] | None = None
    priority: int | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool | None = None


class PricingRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parlor_id: UUID
    name: str
    scope: str
    scope_value: str
    base_rate_paise: int
    time_slabs: list | None = None
    day_of_week_overrides: dict | None = None
    package_defs: list | None = None
    priority: int
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool


class PricePreviewRequest(BaseModel):
    resource_id: UUID | None = None
    resource_type: ResourceType = ResourceType.PC
    zone_id: UUID | None = None
    booking_date: date
    start_time: time
    duration_hours: int = Field(1, ge=1, le=24)
    units: int = Field(1, ge=1, le=50)
    promo_code: str | None = None
    club_customer_id: UUID | None = None


class PricePreviewResponse(BaseModel):
    breakdown: dict
    promotion: dict | None = None
    subtotal_paise: int
    discount_paise: int
    total_paise: int
    total_rupees: str


# --- Promotions ---


class PromotionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    promo_type: PromotionType
    percent_bps: int | None = Field(None, gt=0, le=10000)
    flat_paise: int | None = Field(None, gt=0)
    code: str | None = Field(None, max_length=40)
    max_discount_paise: int | None = Field(None, gt=0)
    min_amount_paise: int | None = Field(None, ge=0)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    happy_hour_start: time | None = None
    happy_hour_end: time | None = None
    usage_limit: int | None = Field(None, gt=0)
    applicable_resource_types: list[ResourceType] | None = None
    min_loyalty_points: int | None = Field(None, ge=0)
    is_active: bool = True


class PromotionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    promo_type: PromotionType | None = None
    percent_bps: int | None = Field(None, gt=0, le=10000)
    flat_paise: int | None = Field(None, gt=0)
    code: str | None = Field(None, max_length=40)
    max_discount_paise: int | None = Field(None, gt=0)
    min_amount_paise: int | None = Field(None, ge=0)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    happy_hour_start: time | None = None
    happy_hour_end: time | None = None
    usage_limit: int | None = Field(None, gt=0)
    applicable_resource_types: list[ResourceType] | None = None
    min_loyalty_points: int | None = Field(None, ge=0)
    is_active: bool | None = None


class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parlor_id: UUID
    name: str
    promo_type: str
    percent_bps: int | None = None
    flat_paise: int | None = None
    code: str | None = None
    max_discount_paise: int | None = None
    min_amount_paise: int | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    happy_hour_start: time | None = None
    happy_hour_end: time | None = None
    usage_limit: int | None = None
    used_count: int
    applicable_resource_types: list | None = None
    min_loyalty_points: int | None = None
    is_active: bool
    disabled_by_platform: bool
    disabled_reason: str | None = None


class PromotionValidateRequest(BaseModel):
    code: str | None = None
    promotion_id: UUID | None = None
    subtotal_paise: int = Field(..., ge=0)
    resource_type: ResourceType = ResourceType.PC
    booking_date: date
    start_time: time
    club_customer_id: UUID | None = None


# --- Owner bookings ---


class WalkInBookingRequest(BaseModel):
    """Create a booking at the counter for someone who is not using the app."""

    resource_id: UUID | None = None
    resource_type: ResourceType = ResourceType.PC
    booking_date: date | None = Field(
        None, description="Defaults to today (IST) when omitted."
    )
    start_time: time | None = Field(
        None, description="Defaults to the current IST hour when omitted."
    )
    duration_hours: int = Field(1, ge=1, le=24)
    units: int = Field(1, ge=1, le=50)
    guest_name: str | None = Field(None, max_length=100)
    contact_phone: str | None = Field(None, max_length=20)
    promo_code: str | None = None
    payment_mode: str = Field("cash", max_length=30)
    #: Check the customer straight in — the usual counter behaviour.
    check_in_now: bool = True


class CancelBookingRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=100)
    detail: str | None = None


class ExtendBookingRequest(BaseModel):
    additional_hours: int = Field(1, ge=1, le=12)


class OwnerBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_ref: str
    parlour_id: UUID
    user_id: UUID | None = None
    resource_id: UUID | None = None
    resource_label: str | None = None
    club_customer_id: UUID | None = None
    customer_name: str | None = None
    contact_phone: str | None = None
    station_type: str | None = None
    slot_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_hours: int | None = None
    units: int | None = None
    booking_status: str
    payment_status: str
    payment_mode: str | None = None
    amount_paise: int | None = None
    club_discount_paise: int = 0
    commission_paise: int | None = None
    is_walk_in: bool = False
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    extended_hours: int = 0
    no_show_at: datetime | None = None
    cancellation_reason: str | None = None
    created_at: datetime | None = None


class LiveOccupantResponse(BaseModel):
    booking_id: UUID
    booking_ref: str
    resource_id: UUID | None = None
    resource_label: str | None = None
    resource_type: str | None = None
    customer_name: str | None = None
    contact_phone: str | None = None
    checked_in_at: datetime | None = None
    ends_at: datetime | None = None
    minutes_remaining: int | None = None
    is_overdue: bool = False
    units: int | None = None
    amount_paise: int | None = None


# --- Customers ---


class CustomerNoteRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class CustomerTagRequest(BaseModel):
    tags: list[str] = Field(..., max_length=20)


class CustomerBanRequest(BaseModel):
    is_banned: bool
    reason: str | None = Field(None, max_length=500)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parlor_id: UUID
    user_id: UUID | None = None
    display_name: str | None = None
    phone: str | None = None
    visit_count: int
    total_spend_paise: int
    total_spend_rupees: str = "0.00"
    last_visit_at: datetime | None = None
    loyalty_points: int
    tags: list | None = None
    notes: str | None = None
    is_banned: bool
    ban_reason: str | None = None
    platform_flagged: bool


class CustomerNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    body: str
    author_id: UUID | None = None
    created_at: datetime


class CustomerDetailResponse(BaseModel):
    customer: CustomerResponse
    recent_bookings: list[OwnerBookingResponse]
    note_history: list[CustomerNoteResponse]


# --- Revenue + occupancy analytics ---


class RevenueSummaryResponse(BaseModel):
    range: str
    from_date: date
    to_date: date
    gross_paise: int
    gross_rupees: str
    commission_paise: int
    net_paise: int
    net_rupees: str
    discount_paise: int
    booking_count: int
    completed_count: int
    cancelled_count: int
    no_show_count: int
    avg_session_paise: int
    by_resource_type: list[dict]
    by_payment_method: list[dict]
    daily: list[dict]


class OccupancyPointResponse(BaseModel):
    bucket_start: datetime
    occupied_minutes: int
    capacity_minutes: int
    utilization_bps: int
    booking_count: int
    revenue_paise: int


class HeatmapCellResponse(BaseModel):
    weekday: int
    hour: int
    occupied_minutes: int
    capacity_minutes: int
    utilization_bps: int
    booking_count: int


class UtilizationRowResponse(BaseModel):
    grain: str
    grain_key: str
    label: str | None = None
    occupied_minutes: int
    capacity_minutes: int
    utilization_bps: int
    booking_count: int
    revenue_paise: int


class NoShowRateResponse(BaseModel):
    from_date: date
    to_date: date
    booking_count: int
    no_show_count: int
    no_show_rate_bps: int
    by_resource_type: list[dict]


# --- Admin oversight ---


class AdminPromotionDisableRequest(BaseModel):
    disabled: bool
    reason: str | None = Field(None, max_length=500)


class AdminResourceDeactivateRequest(BaseModel):
    is_active: bool
    reason: str | None = Field(None, max_length=500)


class AdminCustomerFlagRequest(BaseModel):
    flagged: bool
    reason: str | None = Field(None, max_length=500)


class AdminForceCancelRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=100)
    detail: str | None = None
