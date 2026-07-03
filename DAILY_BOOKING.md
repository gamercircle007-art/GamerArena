# GROK — BOOKING FEATURE DAILY SESSION
# Paste at the start of EVERY Grok session (after first session).
# ─────────────────────────────────────────────────────────────────────────────

You are adding OYO-style gaming parlor booking to the GameConnect/ParLour Flutter + FastAPI app.
All screens mirror OYO hotel booking UX, adapted for gaming stations.

## Context Files
- `GAMING_BOOKING_CONTEXT.md` — full spec: all screens, DB schema, APIs, widgets, nearby calculation
- `PROGRESS_BOOKING.md` — task checklist (find first [ ] and build it)

## Do This Now
```bash
cat PROGRESS_BOOKING.md | grep "^\- \[ \]" | head -5
```
Find first unchecked `[ ]` → read existing relevant files → build it completely → show all code.

## Rules
- ParlourListCard is reusable on BOTH home and search screens. Don't duplicate.
- BookingBottomCTA (price + book button) is one reusable widget used on 5+ screens.
- Nearby search MUST use PostGIS ST_DWithin — never client-side haversine.
- All prices in ₹ Indian format (intl package). Taxes always shown separately.
- Booking ref generated server-side only (never client-generated).
- Free cancellation deadline always displayed. Non-refundable shown in RED.
- OYO red: #E31E24. Confirmed green: #1A7A4A. Cancelled orange: #C0392B.

## Install (if packages not yet added)
```bash
# Flutter
flutter pub add photo_view dots_indicator readmore flutter_rating_bar \
  percent_indicator share_plus url_launcher pinput

# Backend
pip install geoalchemy2  # if not already installed
```

## Run
```bash
uvicorn backend.app.main:app --reload --port 8000   # backend
flutter run                                          # flutter
```

## If Grok Loses Context
```
Re-read GAMING_BOOKING_CONTEXT.md. We were building task [TASK-ID]. Continue.
```

Start → `cat PROGRESS_BOOKING.md` → build next `[ ]`.
