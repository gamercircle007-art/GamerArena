# GAMING PARLOR BOOKING — FULL CONTEXT
# OYO-style booking flow adapted for gaming stations.
# Read this file + PROGRESS_BOOKING.md every session.
# ─────────────────────────────────────────────────────────────────────────────

## WHAT WE'RE BUILDING
An OYO-style booking experience for gaming parlors, covering:
1. Home page — city picker, nearby parlors, quick picks, scrollable cards
2. Search/listing — filters by date, game type, price, distance
3. Parlor detail — photo gallery, ratings, room/slot categories, highlights, why book
4. Booking flow — offers, slot picker, booking summary, pay/book CTA
5. Booking confirmation — payment toggle (pay now / pay at parlor), timer offer
6. Booking details — booking ID, check-in time, cancellation policy, manage booking
7. Cancellation flow — reason picker → sub-reason → confirmed cancelled + refund
8. Reviews & ratings — overall score, category breakdown, individual reviews with photos

---

## DESIGN SYSTEM (OYO-adapted for gaming)

### Colors
```
Primary red:   #E31E24   (OYO red — book buttons, accents)
Header green:  #1A7A4A   (confirmed state)
Header orange: #C0392B   (cancelled state)
Card bg:       #FFFFFF
Page bg:       #F5F5F5
Text dark:     #1A1A1A
Text muted:    #666666
Text light:    #999999
Rating gold:   #F5A623
Discount green:#2E7D32
Tag bg:        #F0FAF5
Border:        #E8E8E8
```

### Typography
- Heading: Inter Bold 22–28px
- Subheading: Inter SemiBold 16–18px
- Body: Inter Regular 14px
- Caption: Inter Regular 12px, color #999

### Bottom CTA Bar (all booking screens)
```
[Price ₹XXX   ₹strikethrough  XX% OFF]   [Book Now & Pay at Parlor — RED BUTTON]
[+ ₹XX taxes & fees]
```

---

## ALL NEW FLUTTER SCREENS TO BUILD

### Screen 1 — HomeScreen (OYO-style)
```
TOP BAR:
  Left: hamburger menu icon
  Center: OYO-style logo → "GameConnect" or "ParLour" logo
  Right: notification bell + profile avatar

SEARCH BAR (prominent, grey background):
  Search icon + "Around your last booking"
  Subtitle: "30 Jun – 1 Jul · 1 Player"
  Tap → SearchScreen

CITY HORIZONTAL SCROLL (circular avatars):
  [📍 Nearby] [Delhi] [Mumbai] [Bangalore] [Pune] [Hyderabad] [Chennai]
  Each: location photo in circle + city name below

QUICK PICKS FOR YOU (tabbed horizontal scroll):
  Tabs: [Recommended] [Past Plays] [Recently Viewed] [Offers]
  Under each tab: 2-column horizontal-scrollable ParlourCard grid

EXCLUSIVE OFFERS SECTION:
  [Book 1 Get 1 Free] [Refer & Play ₹99] — offer banners

BOTTOM NAV: Home | Bookings | Search | OYO Serviced | Under ₹299
```

### Screen 2 — SearchResultsScreen (listing)
```
TOP BAR (condensed search):
  Left: hamburger
  Center: search box (city + dates + players)
  Tappable: goes back to search input

RESULTS COUNT: "X Gaming Stations found · Price per slot per hour"

FILTER BAR (horizontal scroll):
  [Sort ↕] [Selected City ×] [Price ↓] [Date ×] [Game Type] [≡ Filters (badge)]

RESULTS LIST (vertical scroll):
  ParlourListCard per result (see card spec below)
```

### ParlourListCard Spec (reusable, use everywhere)
```
┌─────────────────────────────────────────────┐
│ [HERO IMAGE - full width, 220px tall]        │
│ [Badge: "OYO Serviced" / "Super OYO" TL]   │
│ [♡ Favourite BR]                            │
├─────────────────────────────────────────────┤
│ ⭐ 4.1 (295)  |W| Wizard  |💳| Pay at Parlor│
│ Townhouse Gaming Hub Sector 62 Noida…       │
│ 📍 5.7 km from centre · Gautam Buddh Nagar │
│ 🎮 Free PC · 🏆 Tournament Zone available  │
│ 👥 Couples are welcome   ✅ Breakfast avail │
│ ₹149/hr  ~~₹599~~  75% off                 │
│ + ₹22 taxes & fees                         │
└─────────────────────────────────────────────┘
Tap → ParlourDetailScreen
```

### Screen 3 — ParlourDetailScreen
```
HERO GALLERY (full screen, swipeable):
  Image carousel, count badge "3/35"
  Category thumbnails below: [Room] [Arena] [Reception] [Facade]
  Favourite (♡) + Share (↑) buttons top right

PARLOUR NAME SECTION:
  Badge chip: "OYO Serviced" / "Super Gaming Zone"
  Name: "GameConnect Arena Sector 62 Noida"
  ⭐ 4.1 (295 ratings) · 11 reviews   [tap → RatingsScreen]
  🏆 5.0 · Check-in rating · Delightful experience

ADDRESS:
  Full address text
  [View on map] link → flutter_map full screen

WHY BOOK THIS STATION? section:
  [W] Wizard discount available — up to 10% extra
  [🎮] Well maintained gaming equipment
  [👍] Rated high for location
  [🏆] Rated high for gaming experience

SCROLL → HORIZONTAL TABS:
  [Booking Details] [Offers] [Room Categories/Slots] [Ratings & Reviews]

STICKY BOTTOM BAR:
  ₹149/hr  ~~₹599~~  + ₹22 taxes  [Book Now & Pay at Parlor]
```

### Screen 4 — BookingDetailsTabScreen (Tab 1 of ParlourDetail)
```
BROWSE THROUGH SPECIAL OFFERS section:
  3 offer cards with [Apply / Applied] button:
  ₹149/hr | Pay at parlor | Book now and pay at parlor [Applied]
  ₹129/hr | Pay at parlor | Book now and pay at parlor [Apply]
  ₹134/hr | Pay now       | Save up to 10%            [Apply]
  [View all offers] button

YOUR BOOKING DETAILS section:
  📅 Dates: Tue, 30 Jun – Wed, 1 Jul  [tappable, opens date picker]
  👥 Players: 1 slot • 2 players       [tappable, opens picker]
  👤 Booking for: Manish

HERE'S YOUR GAMING SLOT section:
  Room/slot photo + name

STICKY BOTTOM: ₹149/hr ~~₹599~~  [Book Now & Pay at Parlor]
```

### Screen 5 — BookingConfirmedScreen
```
GREEN HEADER:
  "Your booking is confirmed!"
  Subtitle: "Get ready to play!"

PAY NOW OFFER (if applicable):
  "Pay now and get ₹38 off"
  ⏰ Offer valid till: countdown timer (01h:59m:44s)
  
  [Pay at Parlor     ] [Pay Now — ₹38 Off]  ← toggle cards
   No discount           highlighted/selected
  
  Total amount ℹ    ~~₹777~~  ₹739

  Pay using: [Paytm logo ↓] (expandable list)
  
  [Pay ₹739 now] ← RED BUTTON

PARLOUR DETAILS CARD:
  Name + thumbnail photo
  Full address
  [Directions] [Call Parlor] [Need Help] ← 3 circle buttons

CHECK-IN / CHECKOUT:
  Check-in: Tue, 30 Jun 2026 · 10:00 AM onwards
  [1 Slot]
  Checkout: Wed, 1 Jul 2026 · Before 10:00 AM

BOOKING ID: J9E90916 [copy icon]
```

### Screen 6 — BookingDetailsViewScreen (manage existing booking)
```
GREEN HEADER:
  Parlour name · Dates · Players · Price

BOOKING DETAILS CARD:
  📅 Check-in | [1 Slot] | Checkout
  🔑 Booking ID: XXXX [copy]
  👤 Reserved for: Manish
  🎮 Slots & players: 1 Classic Slot • 2 players
  📞 Contact info: email + phone

OYO RUPEE CASHBACK CARD:
  → GameConnect Credits: Earn 50 GC Points on checkout

WHATSAPP UPDATES TOGGLE

VIEW GUEST POLICY link

CANCELLATION POLICY section:
  ⚠️ "This booking is non-refundable"
  🔒 "Free cancellation was available till X date, X time"
  Details text

MANAGE YOUR BOOKING:
  ⏰ Modify player name  [>]
  📋 Avail GST credit on this booking [>]
  ❌ Cancel booking [>] (red text)
```

### Screen 7 — CancellationReasonScreen
```
BACK arrow

TITLE: "Reason for cancellation"

LIST ITEMS with icons + chevrons:
  😊 Don't need this play option
  📍 Want help with location
  🏷️ Found a better price
  🏢 Facing an issue at the property
  ℹ️ Property details did not match
  😔 Had a different issue
```

### Screen 8 — CancellationDetailScreen
```
BACK arrow

TITLE: "Tell us more about it"

CHIP MULTI-SELECT (pill shaped, toggle):
  "Don't need a gaming session"
  "Didn't like the station or property"
  "Want to change session dates or property"
  "Property manager refused check-in"
  "Equipment not working properly"
  "Price changed after booking"

TEXT AREA: "Something else? Type here (optional)"

CONTACT OPTIONS (list):
  📞 Call property  [>]
  💬 Chat with GC support  [>]

STICKY BOTTOM: [Continue to cancel] — black button
```

### Screen 9 — BookingCancelledScreen
```
ORANGE/RED HEADER:
  "Booking cancelled"

REFUND DETAILS section:
  Refunded Amount ℹ  ₹0

PARLOUR CARD:
  Name + photo
  Address
  [Book again] ← RED BUTTON

CHECK-IN / CHECKOUT (greyed out)
BOOKING ID
RESERVED FOR
ROOMS & GUESTS

NEED HELP? section at bottom
```

### Screen 10 — RatingsReviewsScreen
```
OVERALL SCORE:
  Big number "4.1" + star row + "Very Good"
  "295 ratings · 11 reviews"

CATEGORY BREAKDOWN (2-column grid):
  Gaming Equipment 4.2  |  Staff 4.0
  Location 4.2          |  Facilities 4.2
  Cleanliness 4.2       |  Check-in 5.0

INDIVIDUAL REVIEWS:
  [Reviewer Name] · [Verified Stay ✓ badge]
  ⭐⭐⭐⭐☆ stars
  Review photos (3-thumbnail strip)
  Date text
  "Reviewed on GameConnect / Google"
  👍 helpful button

STICKY BOTTOM: same Book CTA
```

---

## BACKEND NEW DB TABLES

```sql
-- ═══ PARLOUR BOOKING SYSTEM ═══

-- Offers / Pricing plans per parlor
parlour_offers (
  id UUID PK,
  parlour_id UUID FK → parlors,
  title VARCHAR(100),
  offer_type VARCHAR(30),   -- 'pay_now' | 'pay_at_parlor' | 'wizard' | 'early_bird'
  discount_type VARCHAR(20), -- 'percentage' | 'fixed'
  discount_value DECIMAL(10,2),
  price_per_hour DECIMAL(10,2),
  original_price DECIMAL(10,2),
  valid_from TIMESTAMPTZ,
  valid_until TIMESTAMPTZ,
  promo_code VARCHAR(20),
  is_active BOOLEAN DEFAULT true,
  terms TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Slot / Time block bookings (expand existing time_slots + bookings)
-- (If time_slots table exists, alter it — otherwise create fresh)
gaming_slots (
  id UUID PK,
  parlour_id UUID FK → parlors,
  parlour_game_id UUID FK → parlour_games NULLABLE,
  slot_date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  price_per_hour DECIMAL(10,2),
  original_price DECIMAL(10,2),
  max_players INT DEFAULT 1,
  current_bookings INT DEFAULT 0,
  is_available BOOLEAN DEFAULT true,
  INDEX(parlour_id, slot_date)
);

gaming_bookings (
  id UUID PK,
  booking_ref VARCHAR(20) UNIQUE,   -- e.g. J9E90916
  user_id UUID FK → users,
  parlour_id UUID FK → parlors,
  slot_id UUID FK → gaming_slots NULLABLE,
  offer_id UUID FK → parlour_offers NULLABLE,
  guest_name VARCHAR(100),
  num_players INT DEFAULT 1,
  slot_date DATE,
  start_time TIME,
  end_time TIME,
  hours_booked DECIMAL(4,2),
  price_per_hour DECIMAL(10,2),
  total_price DECIMAL(10,2),
  tax_amount DECIMAL(10,2),
  discount_amount DECIMAL(10,2) DEFAULT 0,
  final_price DECIMAL(10,2),
  payment_mode VARCHAR(30) DEFAULT 'pay_at_parlor',  -- pay_at_parlor | razorpay | paytm | upi
  payment_status VARCHAR(20) DEFAULT 'pending',       -- pending | paid | refunded | failed
  payment_id VARCHAR(100),
  booking_status VARCHAR(20) DEFAULT 'confirmed',     -- confirmed | checked_in | completed | cancelled | no_show
  cancellation_reason VARCHAR(100),
  cancellation_detail TEXT,
  cancelled_at TIMESTAMPTZ,
  refund_amount DECIMAL(10,2) DEFAULT 0,
  refund_status VARCHAR(20),                           -- null | processing | refunded
  free_cancellation_before TIMESTAMPTZ,               -- deadline for free cancel
  is_non_refundable BOOLEAN DEFAULT false,
  gc_points_earned INT DEFAULT 0,
  contact_email VARCHAR(200),
  contact_phone VARCHAR(20),
  gstin VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cancellation reasons (lookup table)
cancellation_reasons (
  id UUID PK,
  code VARCHAR(50) UNIQUE,
  label VARCHAR(200),
  icon VARCHAR(50),
  sub_reasons JSONB,                -- array of sub-reason strings
  display_order INT
);

-- GC Points / Credits (like OYO Rupees)
gc_points (
  user_id UUID PK FK → users,
  balance INT DEFAULT 0,
  total_earned INT DEFAULT 0,
  total_spent INT DEFAULT 0
);

gc_points_transactions (
  id UUID PK,
  user_id UUID FK → users,
  booking_id UUID FK → gaming_bookings NULLABLE,
  type VARCHAR(20),    -- 'earn' | 'spend' | 'expire'
  points INT,
  description VARCHAR(200),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Parlour rating category breakdown (expand existing ratings)
-- Add columns to ratings table:
ALTER TABLE ratings ADD COLUMN IF NOT EXISTS equipment_rating DECIMAL(2,1);
ALTER TABLE ratings ADD COLUMN IF NOT EXISTS staff_rating DECIMAL(2,1);
ALTER TABLE ratings ADD COLUMN IF NOT EXISTS location_rating DECIMAL(2,1);
ALTER TABLE ratings ADD COLUMN IF NOT EXISTS cleanliness_rating DECIMAL(2,1);
ALTER TABLE ratings ADD COLUMN IF NOT EXISTS checkin_rating DECIMAL(2,1);
ALTER TABLE ratings ADD COLUMN IF NOT EXISTS is_verified_stay BOOLEAN DEFAULT false;
ALTER TABLE ratings ADD COLUMN IF NOT EXISTS review_photos TEXT[];

-- Add computed columns to parlors:
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS equipment_rating DECIMAL(3,2) DEFAULT 0;
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS staff_rating DECIMAL(3,2) DEFAULT 0;
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS checkin_rating DECIMAL(3,2) DEFAULT 0;
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS is_wizard_enabled BOOLEAN DEFAULT false;
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS is_couples_allowed BOOLEAN DEFAULT true;
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS price_per_hour DECIMAL(10,2);
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS original_price DECIMAL(10,2);
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS discount_percent INT DEFAULT 0;
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS base_tax_rate DECIMAL(4,3) DEFAULT 0.18;

-- User search/booking history
user_search_history (
  id UUID PK,
  user_id UUID FK → users,
  city VARCHAR(100),
  query TEXT,
  searched_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## ALL NEW BACKEND API ENDPOINTS

### Home & Discovery
```
GET  /home                        → featured parlors, quick picks, offers, cities
GET  /home/nearby?lat=&lng=&limit=10   → nearest parlors by user GPS
GET  /home/quick-picks?type=recommended|past_plays|recently_viewed
GET  /cities                      → list of available cities
```

### Search & Listing
```
GET  /parlors/search
     ?city=Delhi
     &lat=28.6&lng=77.2
     &check_in=2025-01-30
     &check_out=2025-01-31
     &num_players=2
     &game_type=PC|Console|VR
     &price_min=100&price_max=500
     &sort=distance|price_asc|price_desc|rating
     &page=1&limit=20
     → PaginatedResponse<ParlourSearchResult> with distance, available_slots_count
```

### Parlor Detail
```
GET  /parlors/{id}/detail         → full detail: photos, amenities, ratings, why_book highlights
GET  /parlors/{id}/slots?date=2025-01-30&num_players=2   → available time slots
GET  /parlors/{id}/offers         → active offers sorted by best price
GET  /parlors/{id}/ratings        → paginated ratings with category breakdown
GET  /parlors/{id}/gallery        → all photos in categories (Room/Arena/Reception/Facade)
```

### Booking Flow
```
POST /bookings
     body: {parlour_id, slot_id?, offer_id?, guest_name, num_players,
            slot_date, start_time, end_time, payment_mode, contact_email, contact_phone}
     → {booking_id, booking_ref, final_price, free_cancellation_before, ...}

GET  /bookings/{id}               → full booking details
GET  /bookings/ref/{ref}          → by reference code (J9E90916)
GET  /users/me/bookings           → my bookings (upcoming | past)

PATCH /bookings/{id}/guest-name   body:{guest_name}
PATCH /bookings/{id}/gstin        body:{gstin}

POST /bookings/{id}/pay           body:{payment_mode, payment_token?}
     → triggers Razorpay/Paytm if pay_now mode

GET  /bookings/{id}/payment-options   → pay_now discount, countdown timer end time

POST /bookings/{id}/cancel
     body:{reason_code, detail_chips:[], additional_text?}
     → {refund_amount, refund_status, cancellation_policy_text}

GET  /cancellation-reasons        → lookup table for reason picker

GET  /users/me/gc-points          → balance + transaction history
```

---

## NEARBY PARLORS — PYTHON CALCULATION FUNCTION

```python
# backend/app/services/geo_service.py — ADD THIS FUNCTION

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint
from ..models.parlor import Parlour

async def get_nearby_parlors_sorted(
    lat: float,
    lng: float,
    db: AsyncSession,
    radius_meters: int = 10000,
    game_type: str = None,
    price_min: float = None,
    price_max: float = None,
    sort_by: str = "distance",
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """
    Returns parlors within radius_meters of (lat, lng),
    sorted by distance or price or rating.
    Attaches distance_km to each result.
    """
    user_point = func.ST_SetSRID(
        func.ST_MakePoint(lng, lat), 4326
    ).cast(Geography)

    distance_expr = func.ST_Distance(
        Parlour.location, user_point
    ).label("distance_meters")

    q = (
        select(Parlour, distance_expr)
        .where(
            func.ST_DWithin(Parlour.location, user_point, radius_meters)
        )
        .where(Parlour.is_active == True)
    )

    if game_type:
        q = q.where(Parlour.game_types.any(game_type))
    if price_min is not None:
        q = q.where(Parlour.price_per_hour >= price_min)
    if price_max is not None:
        q = q.where(Parlour.price_per_hour <= price_max)

    if sort_by == "distance":
        q = q.order_by("distance_meters")
    elif sort_by == "price_asc":
        q = q.order_by(Parlour.price_per_hour.asc())
    elif sort_by == "price_desc":
        q = q.order_by(Parlour.price_per_hour.desc())
    elif sort_by == "rating":
        q = q.order_by(Parlour.avg_rating.desc())

    q = q.offset(offset).limit(limit)

    rows = (await db.execute(q)).all()

    results = []
    for parlor, dist_m in rows:
        dist_km = round(dist_m / 1000, 1)
        results.append({
            "id": str(parlor.id),
            "name": parlor.name,
            "logo_url": parlor.logo_url,
            "address": parlor.address,
            "game_types": parlor.game_types,
            "avg_rating": float(parlor.avg_rating or 0),
            "rating_count": parlor.rating_count or 0,
            "price_per_hour": float(parlor.price_per_hour or 0),
            "original_price": float(parlor.original_price or 0),
            "discount_percent": parlor.discount_percent or 0,
            "is_verified": parlor.is_verified,
            "is_wizard_enabled": parlor.is_wizard_enabled,
            "is_couples_allowed": parlor.is_couples_allowed,
            "distance_km": dist_km,
            "distance_label": f"{dist_km} km from centre",
            "tax_rate": float(parlor.base_tax_rate or 0.18),
        })
    return results


async def get_nearby_count(lat: float, lng: float, db: AsyncSession, radius_meters: int = 10000) -> int:
    """Count of nearby parlors (for search results header)."""
    user_point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326).cast(Geography)
    result = await db.execute(
        select(func.count(Parlour.id)).where(
            func.ST_DWithin(Parlour.location, user_point, radius_meters)
        ).where(Parlour.is_active == True)
    )
    return result.scalar_one()
```

---

## BOOKING REFERENCE GENERATOR
```python
# backend/app/utils/booking_ref.py
import random, string

def generate_booking_ref() -> str:
    """Generates J9E90916 style ref: 1 letter + 1 digit + 1 letter + 5 alphanumeric"""
    prefix = random.choice(string.ascii_uppercase)
    mid = random.randint(0, 9)
    suffix = random.choice(string.ascii_uppercase)
    rest = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}{mid}{suffix}{rest}"
```

---

## FLUTTER PACKAGES TO ADD
```yaml
dependencies:
  # Already present — confirm:
  flutter_map: ^6.1.0
  geolocator: ^11.0.0
  cached_network_image: ^3.3.1
  intl: ^0.19.0
  shimmer: ^3.0.0

  # ADD THESE:
  photo_view: ^0.14.0          # fullscreen photo gallery
  dots_indicator: ^3.0.1       # image carousel dots
  readmore: ^3.0.0             # "Read more" for long text
  flutter_rating_bar: ^4.0.1  # star rating display
  percent_indicator: ^4.2.3   # category rating bars
  countdown_timer_count_down: ^2.0.0  # payment offer countdown
  pinput: ^5.0.0               # OTP / booking ID display (copy)
  share_plus: ^9.0.0           # share booking
  url_launcher: ^6.3.0        # call hotel, directions
```

---

## ANGULAR ADMIN PANEL ADDITIONS

### New Admin Screens
```
/admin/bookings          → All bookings table (filter by status, date, parlor)
/admin/bookings/:id      → Booking detail + management actions
/admin/parlors           → Parlor list (already exists, add pricing + slots)
/admin/slots             → Time slot inventory management
/admin/offers            → Create/manage pricing offers
/admin/cancellations     → Cancellation requests + refund management
/admin/gc-points         → GC Points transactions overview
/admin/reviews           → Review moderation (already partially exists)
```

### New Admin API Endpoints
```
GET  /admin/bookings              ?status=&parlor_id=&date_from=&date_to=&page=
GET  /admin/bookings/:id
PATCH /admin/bookings/:id/status  body:{status, reason?}
GET  /admin/bookings/stats        → today_bookings, revenue_today, cancellations, upcoming
GET  /admin/offers                → all active offers
POST /admin/offers                → create new offer
PATCH /admin/offers/:id
GET  /admin/slots                 → time slot inventory
POST /admin/slots/bulk            → create bulk slots for a parlor
GET  /admin/gc-points/summary     → total points issued, spent, outstanding
```

---

## CODING RULES
1. Use existing Riverpod providers where possible — extend don't replace.
2. ParlourListCard must be a reusable widget used on BOTH home screen and search results.
3. Booking confirmation uses Redis for countdown timer TTL (payment offer expires).
4. Booking ref generated server-side only — never client-generated.
5. Distance calculation always uses PostGIS ST_DWithin + ST_Distance — never client-side haversine.
6. Bottom CTA bar (price + book button) must be a reusable widget used on 5+ screens.
7. All money amounts in INR, formatted as ₹X,XXX (Indian format, intl package).
8. Taxes shown separately always. Final price = base + taxes − discount.
9. Free cancellation deadline always shown if applicable. Non-refundable shown in red.
10. Angular: extend existing data-table pattern — one new booking management screen at a time.

---

## START: `cat PROGRESS_BOOKING.md` → build first unchecked task.
