# Cashfree + Slots + Onboarding — completion checklist

## Implemented

### P0
- [x] Code map `docs/PHASE0_CODE_MAP.md`

### P1 Schema
- [x] Migration `021_cashfree_slots` — parlor_stations, parlor_hours, parlor_closures, booking_holds, payment_ledger, webhook_events, booking_audit, reconciliation_issues
- [x] GamingBooking extensions: station_type, units, amount_paise, cf_order_id, idempotency_key, hold_expires_at

### P2 Slot engine + booking
- [x] `GET /parlors/{id}/availability?date=&station_type=`
- [x] `GET /parlors/{id}/station-types`
- [x] `POST /bookings/v2` + Idempotency-Key + FOR UPDATE + holds (7 min)
- [x] `GET /bookings/{id}/status` (+ Cashfree poll reconcile)
- [x] Materialized fallback slots (`slot_engine`) for legacy UI
- [x] Celery: expire_hold, sweep every 5m, nightly reconciliation

### P3 Cashfree
- [x] `cashfree_client.py` create/get order, webhook HMAC
- [x] `POST /payments/cashfree/bookings/{id}/order`
- [x] `POST /payments/webhooks/cashfree` (store + process)
- [x] Mock mode when keys missing
- [x] Payment ledger rows on confirm
- [ ] Live sandbox UPI E2E (needs your CASHFREE_* keys)
- [ ] Full refund Cashfree API path (cancel still updates local status)

### P4 Flutter
- [x] Station chips, duration, units, live price bar
- [x] Book Now → `/bookings/v2` → status screen polling
- [x] My Bookings existing screen (wired to gaming-bookings)
- [ ] Official Cashfree Flutter SDK UI (mock/pay_at_parlor works without keys)

### P5 Angular
- [x] `/parlors/onboarding` wizard (stations + hours + live preview)
- [ ] Full 5-step parlor create + 2FA + refund admin drawers (partial — payments table via existing bookings)

### P6 Security (partial)
- [x] Server-side amount (paise) for v2
- [x] Idempotency key
- [x] Webhook signature when secret set
- [x] Owner/admin gate on onboarding routes
- [ ] Full IDOR pytest matrix + gitleaks + TOTP

### P7
- [x] Slot inventory for VR GAMING ADDA verified on live API
- [ ] Sandbox ₹ payment with real Cashfree account
