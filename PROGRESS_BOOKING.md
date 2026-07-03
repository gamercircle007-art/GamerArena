# Gaming Parlor Booking — OYO-Style PROGRESS TRACKER
# Grok: `cat PROGRESS_BOOKING.md` → first [ ] → build completely → mark [x] YYYY-MM-DD → next
# Reference: GAMING_BOOKING_CONTEXT.md for full specs
# ─────────────────────────────────────────────────────────────────────────────

## DAILY USAGE
Start: "Read GAMING_BOOKING_CONTEXT.md and PROGRESS_BOOKING.md. Build next unchecked task."
End:   "Mark completed tasks [x] with today's date. Update SESSION LOG table."

---

## PHASE 1 — DATABASE MIGRATIONS (run in order)

- [ ] BK-DB01: Create migration: gaming_slots + gaming_bookings
      File: `alembic revision -m "add_gaming_booking_tables"`
      Tables: gaming_slots, gaming_bookings (full schema in GAMING_BOOKING_CONTEXT.md)
      Add index: gaming_slots(parlour_id, slot_date), gaming_bookings(user_id), gaming_bookings(booking_ref UNIQUE)
      Run: `alembic upgrade head`

- [ ] BK-DB02: Create migration: parlour_offers + cancellation_reasons
      File: `alembic revision -m "add_offers_cancellation_tables"`
      Tables: parlour_offers, cancellation_reasons
      Seed: INSERT default cancellation reasons (6 reasons from screenshots)
      Run: `alembic upgrade head`

- [ ] BK-DB03: Create migration: gc_points + gc_points_transactions
      File: `alembic revision -m "add_gc_points_tables"`
      Tables: gc_points, gc_points_transactions
      Run: `alembic upgrade head`

- [ ] BK-DB04: Create migration: extend existing parlors + ratings tables
      File: `alembic revision -m "extend_parlors_ratings_for_booking"`
      ALTER parlors: add price_per_hour, original_price, discount_percent, base_tax_rate,
                     equipment_rating, staff_rating, checkin_rating,
                     is_wizard_enabled, is_couples_allowed
      ALTER ratings: add equipment_rating, staff_rating, location_rating, cleanliness_rating,
                     checkin_rating, is_verified_stay, review_photos TEXT[]
      ALTER users: add city VARCHAR(100)
      Run: `alembic upgrade head`

- [ ] BK-DB05: Create migration: user_search_history
      File: `alembic revision -m "add_search_history"`
      Table: user_search_history
      Run: `alembic upgrade head`

---

## PHASE 2 — BACKEND MODELS + SCHEMAS

- [ ] BK-BE01: Create backend/app/models/gaming_booking.py
      → GamingSlot, GamingBooking, ParlourOffer, CancellationReason models
      → Use SQLAlchemy 2.0 async patterns
      → GamingBooking: include @property for is_cancellation_free()
        → returns True if NOW() < free_cancellation_before

- [ ] BK-BE02: Create backend/app/models/gc_points.py
      → GCPoints, GCPointsTransaction models

- [ ] BK-BE03: Create backend/app/schemas/booking.py
      → GamingSlotResponse, ParlourOfferResponse, BookingCreateRequest, BookingResponse,
         BookingDetailResponse, BookingSummaryResponse (for list), CancelBookingRequest,
         CancellationReasonResponse, PaymentOptionsResponse, GCPointsResponse

- [ ] BK-BE04: Create backend/app/schemas/parlour_detail.py
      → ParlourDetailResponse (for detail page), ParlourSearchResult (for listing),
         ParlourHighlight, RatingCategoryBreakdown, ReviewItem, ParlourGalleryCategory

---

## PHASE 3 — BACKEND SERVICES

- [ ] BK-BE05: Create/update backend/app/services/geo_service.py
      ADD: get_nearby_parlors_sorted() function (full code in GAMING_BOOKING_CONTEXT.md)
      ADD: get_nearby_count() function
      ADD: get_city_parlors(city_name, ...) function for city-based search
      Also: cache nearby results in Redis (key: nearby:{lat_2dp}:{lng_2dp}:{radius}, TTL=120s)

- [ ] BK-BE06: Create backend/app/services/booking_service.py (NEW or expand existing)
      → create_booking(data, db, redis) — validates slot availability, calculates price, generates ref
      → calculate_price(parlour, offer, hours, num_players) → base, tax, discount, final
      → check_slot_availability(slot_id, date, db) → bool
      → get_payment_options(booking_id, db, redis) → pay_now_price, expiry_time, countdown_seconds
      → complete_payment(booking_id, payment_mode, payment_token, db) → payment result
      → cancel_booking(booking_id, user_id, reason_code, detail, db) → refund_amount
      → award_gc_points(user_id, booking_id, db) → points awarded
      → get_user_bookings(user_id, status_filter, db) → paginated bookings

- [ ] BK-BE07: Create backend/app/services/offer_service.py
      → get_best_offers_for_parlor(parlour_id, date, hours, num_players, db) → sorted offers
      → apply_offer(offer_id, booking_context) → discounted_price
      → validate_offer(offer_id, user_id, db) → bool + reason

- [ ] BK-BE08: Create backend/app/utils/booking_ref.py
      → generate_booking_ref() function (pattern: J9E90916, see GAMING_BOOKING_CONTEXT.md)

---

## PHASE 4 — BACKEND ROUTERS

- [ ] BK-BE09: Create backend/app/routers/home.py
      → GET /home — featured, quick_picks, cities, exclusive_offers
      → GET /home/nearby?lat=&lng=&limit=10
      → GET /home/quick-picks?type=recommended|past_plays|recently_viewed
      → GET /cities — list of cities with parlor counts

- [ ] BK-BE10: Create/update backend/app/routers/parlors.py
      ADD:
      → GET /parlors/search?city=&lat=&lng=&check_in=&check_out=&num_players=&game_type=&price_min=&price_max=&sort=&page=&limit=
         → calls geo_service.get_nearby_parlors_sorted()
         → returns {total_count, items: [ParlourSearchResult]}
      → GET /parlors/{id}/detail
      → GET /parlors/{id}/slots?date=&num_players=
      → GET /parlors/{id}/offers
      → GET /parlors/{id}/gallery
      → GET /parlors/{id}/ratings?page=&limit=

- [ ] BK-BE11: Create backend/app/routers/bookings.py (NEW or expand existing)
      → POST /bookings
      → GET /bookings/{id}
      → GET /bookings/ref/{ref}
      → GET /users/me/bookings?status=upcoming|past&page=
      → PATCH /bookings/{id}/guest-name
      → PATCH /bookings/{id}/gstin
      → POST /bookings/{id}/pay
      → GET /bookings/{id}/payment-options
      → POST /bookings/{id}/cancel
      → GET /cancellation-reasons

- [ ] BK-BE12: Create backend/app/routers/gc_points.py
      → GET /users/me/gc-points
      → GET /users/me/gc-points/transactions

- [ ] BK-BE13: Register all new routers in backend/app/main.py
      → from .routers import home, bookings, gc_points
      → app.include_router(home.router, prefix="/v1", tags=["Home"])
      → app.include_router(bookings.router, prefix="/v1", tags=["Bookings"])
      → app.include_router(gc_points.router, prefix="/v1", tags=["GCPoints"])
      → Verify all routes visible at /docs

---

## PHASE 5 — FLUTTER MODELS + SERVICES

- [ ] BK-FL01: Add/update Flutter models in lib/shared/models/
      → gaming_booking.dart: GamingBooking, GamingSlot, ParlourOffer, PaymentOptions,
                              CancellationReason, CancellationPolicy, BookingSummary
      → parlour_detail.dart: ParlourDetail, ParlourHighlight, ParlourGalleryCategory,
                              RatingBreakdown, ReviewItem
      → parlour_search.dart: ParlourSearchResult, ParlourSearchFilter, NearbyParlour
      → gc_points.dart: GCPoints, GCTransaction
      → home_data.dart: HomeData, QuickPickType, City

- [ ] BK-FL02: Create lib/features/home/data/home_repository.dart
      → getHomeData() → GET /home
      → getNearbyParlors(lat, lng, limit) → GET /home/nearby
      → getQuickPicks(type) → GET /home/quick-picks
      → getCities() → GET /cities

- [ ] BK-FL03: Create lib/features/parlors/data/parlor_search_repository.dart
      → searchParlors(ParlourSearchFilter) → GET /parlors/search
      → getParlourDetail(id) → GET /parlors/{id}/detail
      → getParlourSlots(id, date, numPlayers) → GET /parlors/{id}/slots
      → getParlourOffers(id) → GET /parlors/{id}/offers
      → getParlourGallery(id) → GET /parlors/{id}/gallery
      → getParlourRatings(id, page) → GET /parlors/{id}/ratings

- [ ] BK-FL04: Create lib/features/booking/data/booking_repository.dart
      → createBooking(BookingCreateRequest)
      → getBooking(id), getBookingByRef(ref)
      → getUserBookings(status, page)
      → getPaymentOptions(bookingId)
      → makePayment(bookingId, mode, token)
      → cancelBooking(bookingId, reason, details, additionalText)
      → getCancellationReasons()
      → updateGuestName(bookingId, name)
      → updateGstin(bookingId, gstin)
      → getGCPoints()

---

## PHASE 6 — FLUTTER PROVIDERS (Riverpod)

- [ ] BK-FL05: Create lib/features/home/providers/home_provider.dart
      → homeDataProvider: AsyncNotifier<HomeData> — loads on screen open
      → nearbyParlorsProvider: AsyncNotifier<List<NearbyParlour>>
        → depends on locationProvider (existing)
        → auto-loads when location available
      → quickPicksProvider(QuickPickType): FutureProvider<List<ParlourSearchResult>>
      → citiesProvider: FutureProvider<List<City>>

- [ ] BK-FL06: Create lib/features/parlors/providers/parlor_search_provider.dart
      → searchFilterProvider: StateNotifier<ParlourSearchFilter>
        → updateCity(), updateDates(), updateGameType(), updatePriceRange(), updateSort()
      → searchResultsProvider: AsyncNotifier<PaginatedResponse<ParlourSearchResult>>
        → depends on searchFilterProvider
        → refreshes when filter changes
      → parlourDetailProvider(id): AsyncNotifier<ParlourDetail>
      → parlourSlotsProvider(id, date): FutureProvider<List<GamingSlot>>
      → parlourOffersProvider(id): FutureProvider<List<ParlourOffer>>

- [ ] BK-FL07: Create lib/features/booking/providers/booking_provider.dart
      → activeBookingProvider: StateNotifier<BookingDraft>
        → BookingDraft: {parlour, slot, offer, guestName, numPlayers, paymentMode}
        → setSlot(), setOffer(), setPaymentMode(), setGuestName()
        → calculatePrice() → computed: base, tax, discount, final
      → bookingCreationProvider: AsyncNotifier<GamingBooking?>
        → createBooking() → optimistic UI → API call
      → userBookingsProvider: AsyncNotifier<List<BookingSummary>>
        → load(), cancel(bookingId, reason, ...)
      → paymentOptionsProvider(bookingId): AsyncNotifier<PaymentOptions>
        → auto-refreshes countdown timer every second via Timer
      → cancellationReasonsProvider: FutureProvider<List<CancellationReason>>
      → gcPointsProvider: AsyncNotifier<GCPoints>

---

## PHASE 7 — FLUTTER SHARED WIDGETS

- [ ] BK-FL08: Create lib/shared/widgets/parlour_list_card.dart
      REUSABLE card used on Home + Search results screens.
      Props: ParlourSearchResult parlour, VoidCallback onTap, VoidCallback onFavourite
      DESIGN (exact OYO copy for gaming):
      → Hero image (220px, cached_network_image, shimmer placeholder)
      → Top-left badge: "OYO Serviced" / "Super Gaming Zone" / "Wizard" chip
      → Top-right: ♡ favourite icon button (filled if saved)
      → Rating row: ⭐ 4.1 (295) | [W] Wizard | 💳 Pay at Parlor
      → Name (max 2 lines, bold)
      → 📍 distance_label · city name
      → Amenities row: 🎮 Free PC · 🏆 Tournament Zone (if applicable)
      → Feature chips: "👥 Couples welcome" · "✅ Gaming snacks available"
      → Price row: ₹149/hr ~~₹599~~ 75% off (in green)
      → Tax note: + ₹22 taxes & fees
      Elevation: 2, rounded corners: 12px

- [ ] BK-FL09: Create lib/shared/widgets/booking_bottom_cta.dart
      REUSABLE sticky CTA used on: ParlourDetail, BookingDetails, ConfirmedScreen, DetailsView
      Props: double pricePerHour, double originalPrice, String ctaText, VoidCallback onTap
      DESIGN:
      → Left: ₹149/hr (large, bold) · ~~₹599~~ · 75% off (green text)
      → Small text: + ₹22 taxes & fees
      → Right: [ctaText] — OYO red full-height button
      Height: 70px, white bg, top border

- [ ] BK-FL10: Create lib/shared/widgets/rating_stars.dart
      Props: double rating, int? count, bool showCount, double size
      → Filled/half/empty stars using flutter_rating_bar
      → Optional count in brackets

- [ ] BK-FL11: Create lib/shared/widgets/offer_card.dart
      Props: ParlourOffer offer, bool isApplied, VoidCallback onApply
      DESIGN (OYO style):
      → Left: green % icon circle
      → Center: ₹149/hr | Pay at parlor (bold) / "Book now and pay at parlor"
      → Right: [Applied] grey button OR [Apply] outline button
      → Border: full rounded rectangle card
      Height: 72px

- [ ] BK-FL12: Create lib/shared/widgets/category_rating_bar.dart
      Props: String label, double rating
      → Label left, progress bar center, rating number right
      → Bar fills proportionally to 5.0 max
      → Used in RatingsReviewsScreen category breakdown grid

---

## PHASE 8 — FLUTTER SCREENS

- [ ] BK-FL13: Create lib/features/home/presentation/home_screen.dart
      REPLACE or UPDATE existing home/feed screen with OYO-style home.
      
      SECTIONS (vertical scroll):
        1. AppBar: logo, hamburger, notifications bell
        2. SearchBar (grey card): "Around your last booking" + last search info
           → tap → SearchScreen
        3. City row (horizontal scroll, circular photos):
           [📍 Nearby] [Delhi] [Mumbai] [Bangalore] [Pune] [Hyderabad] [Chennai]
        4. "Quick picks for you" tabs:
           [Recommended] [Past Plays] [Recently Viewed] [Exclusive Offers]
           Each tab: horizontal scroll of 2 ParlourListCards side by side
        5. Exclusive Offers banners (2 horizontal banners)
      
      Bottom nav: Home | Bookings | Search | Nearby | Under ₹299

- [ ] BK-FL14: Create lib/features/parlors/presentation/search_results_screen.dart
      
      TOP (condensed search bar, non-editable, tap to go back):
      FILTER BAR (horizontal scroll chips):
        [Sort ↕ dropdown] [City: Delhi ×] [Price ↓] [Date: 30 Jun ×] [Game Type] [≡ X]
      RESULTS COUNT: "66 Gaming Stations found"
      
      BODY: ListView of ParlourListCard widgets
        → Pull-to-refresh
        → Load-more on scroll end
        → Shimmer skeleton while loading (5 placeholder cards)
        → Empty state: "No stations found" with illustration

- [ ] BK-FL15: Create lib/features/parlors/presentation/search_input_screen.dart
      (Appears when user taps search bar)
      
      → Full screen search with keyboard open
      → City selector: horizontal circle chips (same as home)
      → Date range picker: check-in + check-out calendar
      → Players picker: 1-8 players counter
      → Game type filter chips: PC | Console | VR | Mobile | Board
      → Recent searches list (from user_search_history)
      → [Search] button → navigates to SearchResultsScreen

- [ ] BK-FL16: Create lib/features/parlors/presentation/parlour_detail_screen.dart
      
      PHOTO GALLERY (top):
        → Stack: full-screen SwipeableImage widget
        → Thumbnail strip: [Room] [Arena] [Reception] [Facade] categories
        → "3/35" counter badge
        → ♡ + ↑ buttons top right
        → Close × top left
      
      CONTENT (scrollable below gallery):
        → Badge chip + Name (bold, large)
        → Rating + count + check-in rating bar
        → Address + [View on map] link
        → Divider
        → "Why book this station?" section with 3-4 highlight rows
        → Divider
        → HORIZONTAL SCROLL TABS:
          [Booking Details] [Offers] [Slot Categories] [Ratings & Reviews]
        → Tab content loads in place (not separate routes for tabs)
      
      STICKY BOTTOM: BookingBottomCTA widget

- [ ] BK-FL17: Create lib/features/parlors/presentation/photo_gallery_screen.dart
      → Full-screen PhotoView gallery (photo_view package)
      → Category tabs at top (Room, Arena, etc.)
      → Swipe through all photos
      → Counter badge

- [ ] BK-FL18: Create lib/features/booking/presentation/booking_details_tab.dart
      (Tab 1 of ParlourDetailScreen — "Booking Details" tab content)
      
      OFFERS SECTION:
        → "Browse through special offers"
        → 3 OfferCard widgets
        → [View all offers] button → OffersListScreen
      
      YOUR BOOKING DETAILS section (card):
        → 📅 Dates: [date range] — tappable → date picker dialog
        → 👥 Players: [N slots · N players] — tappable → picker dialog
        → 👤 Booking for: [user name]
      
      YOUR GAMING SLOT section:
        → Slot/room image + name + brief description

- [ ] BK-FL19: Create lib/features/booking/presentation/booking_confirmed_screen.dart
      
      GREEN APPBAR + HEADER:
        → "Your booking is confirmed!" title
        → Subtitle
      
      PAY NOW OFFER CARD (if available):
        → "Pay now and get ₹38 off"
        → ⏰ Countdown timer widget (live, decrements every second)
        → Toggle: [Pay at Parlor | Pay Now ₹38 Off] — segmented control
        → Total amount row
        → Pay using: [Paytm logo ↓] dropdown
        → [Pay ₹739 now] RED BUTTON — only if "Pay now" selected
      
      PARLOUR DETAILS CARD:
        → Name + thumbnail image
        → Full address
        → 3 circle action buttons: [📍 Directions] [📞 Call Parlor] [❓ Need Help]
      
      CHECK-IN / CHECKOUT ROW:
        → Left: Check-in date/time
        → Center: [1 Slot] badge
        → Right: Checkout date/time
      
      BOOKING ID row with copy icon
      
      → On "Pay now" tap: open PaymentBottomSheet → Razorpay/Paytm SDK

- [ ] BK-FL20: Create lib/features/booking/presentation/booking_details_view_screen.dart
      (Shows existing confirmed booking — like OYO "Manage Booking")
      
      GREEN HEADER: parlour name + dates + price
      
      DETAILS CARD: check-in/out, booking ID (copyable), guest name, players
      CONTACT INFO: email + phone
      
      GC CREDITS CARD: "Earn 50 GC Points on checkout" (amber/gold card)
      
      WHATSAPP TOGGLE: "Get booking updates on WhatsApp"
      
      [View guest policy] link
      
      CANCELLATION POLICY SECTION:
        → IF non-refundable: ⚠️ amber warning box "This booking is non-refundable"
        → Free cancellation deadline text (grey)
        → No-show policy text
      
      MANAGE YOUR BOOKING section:
        → ⏰ Modify player name [>]
        → 📋 Avail GST credit [>]
        → ❌ Cancel booking [>] (red text) → CancellationReasonScreen

- [ ] BK-FL21: Create lib/features/booking/presentation/cancellation_reason_screen.dart
      
      BACK arrow + "Reason for cancellation" title
      
      LIST (each a ListTile with icon + text + chevron >):
        → 😊 Don't need this play option
        → 📍 Want help with location
        → 🏷️ Found a better price
        → 🏢 Facing an issue at the property
        → ℹ️ Property details did not match
        → 😔 Had a different issue
      
      → Tap any row → navigate to CancellationDetailScreen(reason: reason)

- [ ] BK-FL22: Create lib/features/booking/presentation/cancellation_detail_screen.dart
      
      BACK arrow + "Tell us more about it" title
      
      CHIP SELECTOR (pill chips, multi-select, toggleable):
        → "Don't need a gaming session"
        → "Didn't like the station or property"
        → "Want to change session dates or property"
        → "Property manager refused check-in"
        → "Equipment not working properly"
        → "Price changed after booking"
      
      OPTIONAL TEXT AREA: "Something else? Type here (optional)"
      
      CONTACT OPTIONS (list rows):
        → 📞 Call property [>]
        → 💬 Chat with GC support [>]
      
      STICKY BOTTOM: [Continue to cancel] black button
        → shows confirm dialog ("Are you sure? Refund: ₹0 (non-refundable)")
        → on confirm → API call → navigate to BookingCancelledScreen

- [ ] BK-FL23: Create lib/features/booking/presentation/booking_cancelled_screen.dart
      
      ORANGE/RED HEADER: "Booking cancelled"
      
      REFUND DETAILS CARD:
        → "Refund details" heading
        → "Refunded Amount ℹ" + "₹0" (or actual amount)
      
      PARLOUR CARD:
        → Name + photo
        → Address
        → [Book again] RED BUTTON
      
      BOOKING SUMMARY (same as confirmed screen, greyed):
        → Check-in/out, Booking ID, Reserved for, Rooms & guests
      
      "NEED HELP?" section: Call + Chat buttons

- [ ] BK-FL24: Create lib/features/parlors/presentation/ratings_reviews_screen.dart
      (Full screen, also used as Tab content in ParlourDetail)
      
      OVERALL SCORE:
        → Big number "4.1" + RatingStars widget + "Very Good" label
        → "295 ratings · 11 reviews"
        → [>] arrow (tap expands details)
      
      CATEGORY BREAKDOWN (2-column grid):
        → Gaming Equipment 4.2 (CategoryRatingBar widget)
        → Staff 4.0
        → Location 4.2
        → Facilities 4.2
        → Cleanliness 4.2
        → Check-in 5.0
      
      REVIEWS LIST:
        → Each review card:
          - Reviewer name + "✓ Verified Stay" badge
          - Star rating row
          - Review photos (3 small thumbnails, tap → full screen)
          - Review text (with ReadMore widget)
          - Date + "Reviewed on GameConnect / Google" logo
          - 👍 Helpful button
      
      STICKY BOTTOM: BookingBottomCTA

- [ ] BK-FL25: Create lib/features/booking/presentation/my_bookings_screen.dart
      
      TABS: [Upcoming] [Past] [Cancelled]
      
      UPCOMING tab:
        → Each booking card: parlour image + name + dates + booking ID + status badge
        → [View/Manage] button → BookingDetailsViewScreen
      
      PAST tab:
        → Same card + [Rate your stay] button if no review yet
      
      CANCELLED tab:
        → Each card + [Book again] button

---

## PHASE 9 — INTEGRATE INTO EXISTING APP

- [ ] BK-FL26: Update lib/app.routes.ts / app_router.dart
      Add all new routes:
      → /home-booking (new OYO-style home)
      → /search-input
      → /search-results
      → /parlour/:id/detail
      → /parlour/:id/gallery
      → /booking/confirm (receives booking data)
      → /booking/:id/details
      → /booking/:id/cancel-reason
      → /booking/:id/cancel-detail
      → /booking/:id/cancelled
      → /my-bookings
      → /ratings/:parlourId

- [ ] BK-FL27: Update existing bottom navigation
      Replace/update existing bottom nav to match OYO tabs:
      → 🏠 Home | 📋 Bookings | 🔍 Search | 🎮 Nearby | 🏷️ Under ₹299

- [ ] BK-FL28: Wire up existing ParlourCard (if any) → replace with new ParlourListCard
      Search codebase for any existing parlour/booking cards and replace with new unified widget.

---

## PHASE 10 — ANGULAR ADMIN PANEL ADDITIONS

- [ ] BK-AD01: Add bookings route + screen to Angular admin
      File: src/pages/bookings/ (already in PROGRESS_ADMIN.md, but extend it)
      Add:
        → BookingStatusBadge component (confirmed/cancelled/completed/no-show)
        → BookingDateFilter in filter bar
        → Revenue total in header (sum of final_price for filtered results)

- [ ] BK-AD02: Create src/pages/slots/SlotsPage.tsx (Angular: slots.component.ts)
      → Date picker + parlor picker filter
      → DataTable: Parlor | Date | Time | Price | Max Players | Booked | Available | Actions
      → "Add Slots" FAB → bulk slot creation form (date range + time range + parlor select)
      → Toggle availability per slot

- [ ] BK-AD03: Create src/pages/offers/OffersPage (Angular: offers.component.ts)
      → DataTable: Parlor | Offer Title | Type | Price | Discount | Valid Until | Active | Actions
      → Create Offer form: parlour select, offer type, price, discount %, validity dates
      → Toggle active/inactive

- [ ] BK-AD04: Create booking cancellation management in Angular admin
      Add to BookingsPage:
      → Filter: "Pending refund" tab
      → Action: "Process refund" button → PATCH /admin/bookings/{id}/status {status:'refunded', amount}
      → Cancellation reason shown in row detail expand

- [ ] BK-AD05: Add revenue analytics to Analytics page (existing)
      ADD to admin analytics:
      → Daily revenue chart (bookings × final_price)
      → Top parlors by revenue
      → Booking conversion rate (searches → bookings)
      → Cancellation rate card

- [ ] BK-AD06: Add new admin API endpoints to backend
      All routes in GAMING_BOOKING_CONTEXT.md under "Angular Admin Panel"
      File: backend/app/routers/admin.py (extend existing)

---

## PHASE 11 — POLISH + TESTING

- [ ] BK-PL01: Add shimmer loading to all new screens (no blank flash)
- [ ] BK-PL02: Add pull-to-refresh to: HomeScreen, SearchResults, MyBookings
- [ ] BK-PL03: Add empty states to all listing screens
- [ ] BK-PL04: Add error retry to all async screens
- [ ] BK-PL05: Test full booking flow: Search → Detail → Offers → Book → Confirmed → Details → Cancel → Cancelled
- [ ] BK-PL06: Test nearby search with mock lat/lng (Delhi: 28.6139, 77.2090)
      → Verify PostGIS ST_DWithin returns correct results
      → Verify distance_km values are reasonable
- [ ] BK-PL07: Test price calculation: base + 18% GST − discount = final
- [ ] BK-PL08: Test countdown timer on payment screen (should reach 0 and disable offer)
- [ ] BK-PL09: Test booking reference uniqueness (run 100 generations, check no collisions)
- [ ] BK-PL10: Responsive layout: all new screens work on Android + iOS + web

---

## SESSION LOG
| Date | Tasks Completed | Next Task | Notes |
|------|----------------|-----------|-------|
| Day 0 | Planning | BK-DB01 | Start with migrations |
| 2026-07-01 | BK-DB01–BK-PL10 (full OYO booking stack) | — | Backend migrations 010–014, gaming_booking domain, Flutter screens/widgets, Angular admin slots/offers. Run `alembic upgrade head` when Postgres is up. |
