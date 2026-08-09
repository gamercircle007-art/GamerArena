"""Booking lock unit tests — hold helpers + SQLite smoke.

Phase 2 acceptance gate (100 concurrent holds → exactly 1) requires Postgres
EXCLUDE and lives in test_booking_lock_pg.py (skipped without DATABASE_URL pg).
"""

from __future__ import annotations

from datetime import date, time

from app.domains.common.exceptions import ConflictError
from app.domains.gaming_booking.lock_service import HOLD_MINUTES, build_during, _is_exclusion_violation


def test_build_during_half_open_one_hour() -> None:
    start, end = build_during(date(2026, 8, 10), time(10, 0), 1)
    assert (end - start).total_seconds() == 3600
    assert start.tzinfo is not None


def test_hold_ttl_is_eight_minutes() -> None:
    assert HOLD_MINUTES == 8


def test_exclusion_detection() -> None:
    class Orig:
        sqlstate = "23P01"

    class Exc(Exception):
        orig = Orig()

    assert _is_exclusion_violation(Exc())
    assert _is_exclusion_violation(Exception("excl_booking_unit_locks_overlap"))


def test_conflict_error_code() -> None:
    err = ConflictError("taken")
    assert err.code == "conflict"
