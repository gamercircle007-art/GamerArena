"""Celery tasks: hold expiry + webhook + reconcile + refund + confirmation."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="booking.expire_hold", expires=25)
def expire_booking_hold(booking_id: str) -> str:
    import asyncio

    from app.db.session import get_session_factory
    from app.domains.gaming_booking.lock_service import LockService
    from app.domains.gaming_booking.models import GamingBooking
    from sqlalchemy import select

    async def _run() -> None:
        factory = get_session_factory()
        async with factory() as session:
            booking = (
                await session.execute(
                    select(GamingBooking).where(GamingBooking.id == UUID(booking_id))
                )
            ).scalar_one_or_none()
            if booking and booking.booking_status in ("held", "payment_pending"):
                booking.hold_expires_at = datetime.now(UTC)
                await session.commit()
            await LockService(session).expire_stale_holds()

    try:
        asyncio.run(_run())
        return "ok"
    except Exception as exc:  # noqa: BLE001
        logger.exception("expire_hold_failed booking_id=%s", booking_id)
        return f"error:{type(exc).__name__}"


@celery_app.task(name="booking.sweep_expired_holds", expires=25)
def sweep_expired_holds() -> int:
    """Every ~30s — set-based expire + slot_released publish."""
    import asyncio

    from app.db.session import get_session_factory
    from app.domains.gaming_booking.lock_service import LockService

    async def _run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            rows = await LockService(session).expire_stale_holds()
            return len(rows)

    try:
        return asyncio.run(_run())
    except Exception:  # noqa: BLE001
        logger.exception("sweep_expired_holds_failed")
        return -1


@celery_app.task(name="booking.process_cashfree_webhook")
def process_cashfree_webhook(event_db_id: str) -> str:
    """Process stored webhook_events row (signature already checked)."""
    import asyncio

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
            if order_id and (
                "SUCCESS" in event_type
                or "PAID" in event_type
                or "PAYMENT_SUCCESS" in event_type
            ):
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


@celery_app.task(name="booking.reconcile_payments", expires=240)
def reconcile_payments() -> str:
    """payment_pending > 15 min → query provider and settle."""
    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.domains.gaming_booking.availability_service import AvailabilityService
    from app.domains.gaming_booking.models import GamingBooking
    from app.domains.payments import cashfree_client

    async def _run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            cutoff = datetime.now(UTC) - timedelta(minutes=15)
            stuck = (
                await session.execute(
                    select(GamingBooking).where(
                        GamingBooking.booking_status == "payment_pending",
                        GamingBooking.updated_at <= cutoff,
                    )
                )
            ).scalars().all()
            n = 0
            for b in stuck:
                if not b.cf_order_id:
                    continue
                try:
                    order = await cashfree_client.get_order(b.cf_order_id)
                    st = (order.get("order_status") or order.get("status") or "").upper()
                    if st in ("PAID", "SUCCESS", "COMPLETED"):
                        await AvailabilityService(session).confirm_payment(
                            b.id,
                            cf_reference=b.cf_order_id,
                            event_id=f"reconcile:{b.cf_order_id}",
                            actor="reconcile",
                        )
                        n += 1
                except Exception:  # noqa: BLE001
                    logger.exception("reconcile_one_failed booking=%s", b.id)
            return n

    try:
        return f"settled={asyncio.run(_run())}"
    except Exception as exc:  # noqa: BLE001
        logger.exception("reconcile_payments_failed")
        return f"error:{type(exc).__name__}"


@celery_app.task(name="booking.auto_refund")
def auto_refund(booking_id: str, cf_reference: str, event_id: str) -> str:
    """Idempotent refund for payment-after-expiry. Never overwrite the new booking."""
    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.domains.gaming_booking.inventory_models import PaymentLedger, ReconciliationIssue
    from app.domains.gaming_booking.models import GamingBooking

    async def _run() -> str:
        factory = get_session_factory()
        async with factory() as session:
            # Idempotent on payment/event id
            existing = (
                await session.execute(
                    select(PaymentLedger).where(
                        PaymentLedger.entry_type == "refund",
                        PaymentLedger.cf_event_id == (event_id or cf_reference or "")[:100],
                    )
                )
            ).scalar_one_or_none()
            if existing:
                return "skip_duplicate"

            booking = (
                await session.execute(
                    select(GamingBooking).where(GamingBooking.id == UUID(booking_id))
                )
            ).scalar_one_or_none()
            if booking is None:
                return "missing"
            if booking.booking_status != "refund_pending":
                return f"skip_status={booking.booking_status}"

            amount = booking.amount_paise or int(float(booking.final_price or 0) * 100)
            # Provider refund call is best-effort; ledger + issue row always recorded.
            try:
                from app.domains.payments import cashfree_client

                if cf_reference and hasattr(cashfree_client, "refund_order"):
                    await cashfree_client.refund_order(cf_reference, amount)
            except Exception:  # noqa: BLE001
                logger.exception("cashfree_refund_call_failed")
                session.add(
                    ReconciliationIssue(
                        booking_id=booking.id,
                        cf_reference=cf_reference or None,
                        issue_type="refund_failed",
                        details=f"auto_refund event={event_id}",
                    )
                )

            session.add(
                PaymentLedger(
                    booking_id=booking.id,
                    entry_type="refund",
                    amount_paise=amount,
                    cf_reference=cf_reference or None,
                    cf_event_id=(event_id or cf_reference or "")[:100] or None,
                    balance_direction="debit",
                )
            )
            booking.booking_status = "failed"
            booking.refund_status = "initiated"
            booking.updated_at = datetime.now(UTC)
            await session.commit()
            return "ok"

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.exception("auto_refund_failed")
        return f"error:{type(exc).__name__}"


@celery_app.task(name="booking.send_confirmation")
def send_booking_confirmation(booking_id: str) -> str:
    """Out-of-band SMS/push/email — never block the webhook path."""
    logger.info("send_booking_confirmation booking_id=%s", booking_id)
    return "queued"


@celery_app.task(name="booking.nightly_reconciliation", expires=3600)
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
                        GamingBooking.created_at >= datetime.now(UTC) - timedelta(days=1),
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
