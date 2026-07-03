"""Seed cancellation reasons, demo slots, and offers for local dev."""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import date, time, timedelta
from decimal import Decimal
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.db import session as db_session
from app.domains.gaming_booking.models import CancellationReason, GamingSlot, ParlourOffer
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension


CANCELLATION_REASONS = [
    ("Don't need play option", False, 1),
    ("Need help with location", False, 2),
    ("Found a better price", False, 3),
    ("Property issue", True, 4),
    ("Details mismatch", True, 5),
    ("Different issue", True, 6),
]


async def seed() -> None:
    factory = db_session.get_session_factory()
    async with factory() as session:
        existing = await session.scalar(select(CancellationReason.id).limit(1))
        if existing is None:
            for label, requires_detail, sort_order in CANCELLATION_REASONS:
                session.add(
                    CancellationReason(
                        label=label,
                        requires_detail=requires_detail,
                        sort_order=sort_order,
                    )
                )

        place = await session.scalar(select(GamingPlace).limit(1))
        if place is None:
            await session.commit()
            print("No gaming places — skip slot/offer seed")
            return

        ext = await session.get(GamingPlaceExtension, place.id)
        if ext is None:
            ext = GamingPlaceExtension(gaming_place_id=place.id)
            session.add(ext)
        ext.price_per_hour = Decimal("149")
        ext.original_price = Decimal("599")
        ext.discount_percent = 75
        ext.base_tax_rate = Decimal("0.18")
        ext.is_wizard_enabled = True
        ext.is_couples_allowed = True

        slot_exists = await session.scalar(
            select(GamingSlot.id).where(GamingSlot.parlour_id == place.id).limit(1)
        )
        if slot_exists is None:
            today = date.today()
            for day_offset in range(3):
                slot_date = today + timedelta(days=day_offset)
                for hour in (10, 14, 18):
                    session.add(
                        GamingSlot(
                            parlour_id=place.id,
                            slot_date=slot_date,
                            start_time=time(hour, 0),
                            end_time=time(hour + 2, 0),
                            price_per_hour=Decimal("149"),
                            original_price=Decimal("599"),
                            max_players=4,
                        )
                    )

        offer_exists = await session.scalar(
            select(ParlourOffer.id).where(ParlourOffer.parlour_id == place.id).limit(1)
        )
        if offer_exists is None:
            session.add(
                ParlourOffer(
                    parlour_id=place.id,
                    title="Pay at Parlor",
                    description="Book now and pay at parlor",
                    discount_percent=Decimal("0"),
                    is_active=True,
                )
            )
            session.add(
                ParlourOffer(
                    parlour_id=place.id,
                    title="Pay Now — Save 10%",
                    description="Pay online for extra discount",
                    discount_percent=Decimal("10"),
                    is_active=True,
                )
            )

        await session.commit()
        print(f"Gaming booking seed OK — venue: {place.name} ({place.id})")


if __name__ == "__main__":
    asyncio.run(seed())