"""OYO-style gaming parlor booking Pydantic schemas."""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Slots ---


class GamingSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parlour_id: UUID
    slot_date: date
    start_time: time
    end_time: time
    price_per_hour: Decimal
    original_price: Decimal | None = None
    max_players: int
    current_bookings: int
    is_available: bool


class SlotListResponse(BaseModel):
    parlour_id: UUID
    slot_date: date | None = None
    slots: list[GamingSlotResponse]


# --- Offers ---


class ParlourOfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parlour_id: UUID
    title: str
    description: str | None = None
    code: str | None = None
    discount_percent: Decimal
    discount_amount: Decimal | None = None
    min_hours: Decimal | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool


class OfferListResponse(BaseModel):
    parlour_id: UUID
    offers: list[ParlourOfferResponse]


# --- Ratings ---


class ParlourRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    gaming_place_id: UUID
    rating: Decimal
    review_text: str | None = None
    equipment_rating: Decimal | None = None
    staff_rating: Decimal | None = None
    location_rating: Decimal | None = None
    cleanliness_rating: Decimal | None = None
    checkin_rating: Decimal | None = None
    is_verified_stay: bool
    review_photos: list[str] = Field(default_factory=list)
    created_at: datetime


class ParlourRatingsSummary(BaseModel):
    average_rating: float | None = None
    total_reviews: int = 0
    equipment_rating: float | None = None
    staff_rating: float | None = None
    location_rating: float | None = None
    cleanliness_rating: float | None = None
    checkin_rating: float | None = None
    reviews: list[ParlourRatingResponse] = Field(default_factory=list)


# --- Parlor detail (OYO style) ---


class ParlourDetailResponse(BaseModel):
    id: UUID
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    lat: float | None = None
    lng: float | None = None
    rating: float | None = None
    phone: str | None = None
    website: str | None = None
    images: list[str] = Field(default_factory=list)
    is_verified: bool = False
    is_open: bool = True
    price_per_hour: Decimal | None = None
    original_price: Decimal | None = None
    discount_percent: Decimal | None = None
    base_tax_rate: Decimal = Decimal("18")
    equipment_rating: float | None = None
    staff_rating: float | None = None
    checkin_rating: float | None = None
    is_wizard_enabled: bool = False
    is_couples_allowed: bool = False
    game_types: list[str] = Field(default_factory=list)
    distance_meters: float | None = None


class ParlourGalleryResponse(BaseModel):
    parlour_id: UUID
    images: list[str] = Field(default_factory=list)


class ParlourSearchItem(ParlourDetailResponse):
    pass


class ParlourSearchResult(BaseModel):
    items: list[ParlourSearchItem]
    total: int
    page: int
    limit: int
    has_more: bool


# --- Booking ---


class CreateGamingBookingRequest(BaseModel):
    parlour_id: UUID
    slot_id: UUID
    offer_id: UUID | None = None
    num_players: int = Field(default=1, ge=1, le=20)
    guest_name: str | None = Field(default=None, max_length=100)
    contact_email: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, max_length=20)
    payment_mode: str = Field(default="pay_at_parlor", max_length=30)


class PriceBreakdown(BaseModel):
    price_per_hour: Decimal
    hours_booked: Decimal
    num_players: int
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    final_price: Decimal


class GamingBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_ref: str
    user_id: UUID
    parlour_id: UUID
    parlour_name: str | None = None
    slot_id: UUID | None = None
    offer_id: UUID | None = None
    guest_name: str | None = None
    num_players: int
    slot_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    hours_booked: Decimal | None = None
    price_per_hour: Decimal | None = None
    total_price: Decimal | None = None
    tax_amount: Decimal | None = None
    discount_amount: Decimal
    final_price: Decimal | None = None
    payment_mode: str
    payment_status: str
    payment_id: str | None = None
    booking_status: str
    cancellation_reason: str | None = None
    cancellation_detail: str | None = None
    cancelled_at: datetime | None = None
    refund_amount: Decimal
    refund_status: str | None = None
    free_cancellation_before: datetime | None = None
    is_non_refundable: bool
    is_cancellation_free: bool
    gc_points_earned: int
    contact_email: str | None = None
    contact_phone: str | None = None
    gstin: str | None = None
    station_type: str | None = None
    duration_hours: int | None = None
    units: int | None = None
    amount_paise: int | None = None
    cf_order_id: str | None = None
    payment_session_id: str | None = None
    hold_expires_at: datetime | None = None
    created_at: datetime


class GamingBookingListResponse(BaseModel):
    items: list[GamingBookingResponse]
    total: int


class UpdateGuestNameRequest(BaseModel):
    guest_name: str = Field(..., min_length=1, max_length=100)


class UpdateGstinRequest(BaseModel):
    gstin: str = Field(..., min_length=15, max_length=20)


class PaymentOption(BaseModel):
    mode: str
    label: str
    description: str
    is_available: bool = True


class PaymentOptionsResponse(BaseModel):
    booking_id: UUID
    options: list[PaymentOption]


class CompletePaymentRequest(BaseModel):
    order_id: str | None = None
    payment_id: str | None = None
    signature: str | None = None


class CompletePaymentResponse(BaseModel):
    booking: GamingBookingResponse
    gc_points_earned: int


class CancelBookingRequest(BaseModel):
    reason_id: UUID | None = None
    cancellation_reason: str | None = Field(default=None, max_length=100)
    cancellation_detail: str | None = None


class CancellationReasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str
    requires_detail: bool
    sort_order: int


# --- GC Points ---


class GCPointsResponse(BaseModel):
    user_id: UUID
    balance: int
    lifetime_earned: int
    updated_at: datetime


class GCPointsTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    amount: int
    transaction_type: str
    booking_id: UUID | None = None
    description: str | None = None
    created_at: datetime


class GCPointsTransactionsResponse(BaseModel):
    items: list[GCPointsTransactionResponse]
    total: int


# --- Home ---


class HomeParlorCard(BaseModel):
    id: UUID
    name: str
    image_url: str | None = None
    rating: float | None = None
    price_per_hour: Decimal | None = None
    original_price: Decimal | None = None
    discount_percent: Decimal | None = None
    distance_meters: float | None = None
    city: str | None = None
    is_verified: bool = False


class HomeResponse(BaseModel):
    nearby_count: int = 0
    featured: list[HomeParlorCard] = Field(default_factory=list)
    quick_picks: list[HomeParlorCard] = Field(default_factory=list)
    nearby_parlors: list[HomeParlorCard] = Field(default_factory=list)
    city: str | None = None
    cities: list["CityItem"] = Field(default_factory=list)
    pick_filter: str = "recommended"
    radius_meters: float | None = None
    posts: list["HomePostItem"] = Field(default_factory=list)


class HomePostItem(BaseModel):
    id: UUID
    content: str
    media_urls: list[str] = Field(default_factory=list)
    parlor_id: UUID
    parlor_name: str
    parlor_logo_url: str | None = None
    parlor_verified: bool = False
    likes_count: int = 0
    comments_count: int = 0
    created_at: datetime


class CityItem(BaseModel):
    name: str
    parlour_count: int = 0
    image_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CitiesResponse(BaseModel):
    cities: list[CityItem]


# --- Admin ---


class AdminOfferCreate(BaseModel):
    parlour_id: UUID
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    code: str | None = None
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    discount_amount: Decimal | None = Field(default=None, ge=0)
    min_hours: Decimal | None = Field(default=None, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool = True


class AdminSlotCreate(BaseModel):
    parlour_id: UUID
    slot_date: date
    start_time: time
    end_time: time
    price_per_hour: Decimal = Field(..., gt=0)
    original_price: Decimal | None = Field(default=None, gt=0)
    max_players: int = Field(default=1, ge=1, le=50)


class AdminGCPointsAdjust(BaseModel):
    user_id: UUID
    amount: int
    description: str | None = None