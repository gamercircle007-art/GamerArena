"""Generate OYO-style booking reference codes (e.g. J9E90916)."""

import random
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_booking.models import GamingBooking

_LETTERS = string.ascii_uppercase
_DIGITS = string.digits


def _random_segment() -> str:
    """Pattern: letter + digit + letter + 5 digits → J9E90916."""
    return (
        random.choice(_LETTERS)
        + random.choice(_DIGITS)
        + random.choice(_LETTERS)
        + "".join(random.choices(_DIGITS, k=5))
    )


async def generate_booking_ref(session: AsyncSession, *, max_attempts: int = 10) -> str:
    """Return a unique booking reference not already in ``gaming_bookings``."""
    for _ in range(max_attempts):
        ref = _random_segment()
        result = await session.execute(
            select(GamingBooking.id).where(GamingBooking.booking_ref == ref).limit(1)
        )
        if result.scalar_one_or_none() is None:
            return ref
    raise RuntimeError("Failed to generate unique booking reference")