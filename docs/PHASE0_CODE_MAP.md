# PHASE 0 — Code map (Cashfree + slots)

## Backend
| Area | Path |
|---|---|
| Parlor slots API | `GET /api/v1/parlors/{id}/slots` → `gaming_booking/parlor_router.py` → `ParlourBookingViewService.get_slots` |
| Slot materialization | `gaming_booking/slot_engine.py` (auto-create hourly slots if empty) |
| Bookings | `POST /api/v1/gaming-bookings` (check router prefix) + `GamingBookingService.create_booking` |
| Models | `gaming_slots`, `gaming_bookings`, `parlour_offers` |
| Payments | `payments/cashfree_client.py`, `payments/router.py` (`/payments/cashfree/*`, webhook) |
| Legacy PG | `payments/razorpay_stub.py` (parked) |

## Flutter
| Area | Path |
|---|---|
| Parlor detail + Slots tab | `features/parlors/presentation/parlour_detail_screen.dart` |
| Slot fetch | `features/booking/data/gaming_booking_repository.dart` → `/parlors/{id}/slots` |
| Draft / confirm | `gaming_booking_provider.dart`, booking confirm screens |
| My Bookings | `features/booking/presentation/gaming_my_bookings_screen.dart` |

## Why screenshots showed empty
- `gaming_slots` table had no rows for VR GAMING ADDA / date.
- UI already correct — inventory missing. **SlotEngine.ensure_slots_for_date** fills on first GET.

## Deviations from full spec (pragmatic ship)
- Virtual slots still **materialized** into `gaming_slots` for compatibility with existing `slot_id` booking path (not pure virtual-only).
- Cashfree: client + create order + webhook ack; full ledger/holds/Celery expiry deferred.
- Angular onboarding wizard deferred (admin can use main API + seed).
