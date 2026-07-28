"""Celery tasks: hold expiry + webhook processing + reconciliation."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="booking.expire_hold")
def expire_booking_hold(booking_id: str) -> str:
    import asyncio

    from app.db.session import get_session_factory
    from app.domains.gaming_booking.availability_service import AvailabilityService

    async def _run() -> None:
        factory = get_session_factory()
        async with factory() as session:
            await AvailabilityService(session).expire_hold(UUID(booking_id))

    try:
        asyncio.run(_run())
        return "ok"
    except Exception as exc:  # noqa: BLE001
        logger.exception("expire_hold_failed booking_id=%s", booking_id)
        return f"error:{type(exc).__name__}"


@celery_app.task(name="booking.sweep_expired_holds")
def sweep_expired_holds() -> int:
    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.domains.gaming_booking.availability_service import AvailabilityService
    from app.domains.gaming_booking.inventory_models import BookingHold

    async def _run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            rows = (
                await session.execute(
                    select(BookingHold).where(
                        BookingHold.released.is_(False),
                        BookingHold.expires_at <= datetime.now(UTC),
                    )
                )
            ).scalars().all()
            n = 0
            svc = AvailabilityService(session)
            for h in rows:
                await svc.expire_hold(h.booking_id)
                n += 1
            return n

    try:
        return asyncio.run(_run())
    except Exception:  # noqa: BLE001
        logger.exception("sweep_expired_holds_failed")
        return -1


@celery_app.task(name="booking.process_cashfree_webhook")
def process_cashfree_webhook(event_db_id: str) -> str:
    """Process stored webhook_events row (signature already checked)."""
    import asyncio
    import json

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.domains.gaming_booking.availability_service import AvailabilityService
    from app.domains.gaming_booking.inventory_models import WebhookEvent
    from app.domains.gaming_booking.models import GamingBooking

    async def _run() -> str:
        factory = get_session_factory()
        async with factory() as session:
            ev = (
                await session.execute(
                    select(WebhookEvent).where(WebhookEvent.id == UUID(event_db_id))
                )
            ).scalar_one_or_none()
            if ev is None or ev.processed:
                return "skip"
            payload = ev.payload or {}
            data = payload.get("data") or payload
            order = data.get("order") or data
            order_id = (
                order.get("order_id")
                or data.get("order_id")
                or payload.get("order_id")
            )
            event_type = (ev.event_type or "").upper()
            if order_id and ("SUCCESS" in event_type or "PAID" in event_type or "PAYMENT_SUCCESS" in event_type):
                booking = (
                    await session.execute(
                        select(GamingBooking).where(
                            (GamingBooking.cf_order_id == order_id)
                            | (GamingBooking.booking_ref == order_id)
                        )
                    )
                ).scalar_one_or_none()
                if booking:
                    await AvailabilityService(session).confirm_payment(
                        booking.id,
                        cf_reference=order_id,
                        event_id=ev.event_id,
                        actor="webhook",
                    )
            ev.processed = True
            await session.commit()
            return "ok"

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.exception("process_webhook_failed")
        return f"error:{type(exc).__name__}"


@celery_app.task(name="booking.nightly_reconciliation")
def nightly_reconciliation() -> str:
    """Placeholder reconciliation — flags unmatched paid bookings without ledger."""
    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.domains.gaming_booking.inventory_models import PaymentLedger, ReconciliationIssue
    from app.domains.gaming_booking.models import GamingBooking

    async def _run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            paid = (
                await session.execute(
                    select(GamingBooking).where(
                        GamingBooking.payment_status == "paid",
                        GamingBooking.created_at
                        >= datetime.now(UTC) - timedelta(days=1),
                    )
                )
            ).scalars().all()
            n = 0
            for b in paid:
                ledger = (
                    await session.execute(
                        select(PaymentLedger).where(
                            PaymentLedger.booking_id == b.id,
                            PaymentLedger.entry_type == "payment",
                        )
                    )
                ).scalar_one_or_none()
                if ledger is None:
                    session.add(
                        ReconciliationIssue(
                            booking_id=b.id,
                            cf_reference=b.cf_order_id,
                            issue_type="paid_without_ledger",
                            details=f"booking_ref={b.booking_ref}",
                        )
                    )
                    n += 1
            await session.commit()
            return n

    try:
        count = asyncio.run(_run())
        return f"issues={count}"
    except Exception as exc:  # noqa: BLE001
        logger.exception("reconciliation_failed")
        return f"error:{type(exc).__name__}"
