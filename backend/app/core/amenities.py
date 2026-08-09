"""Amenity bitmask for discovery filters.

Filter predicate: ``amenities_mask & :mask = :mask`` (no join).
Keep in sync with ``frontend/gamer_circle/lib/core/amenities.dart``.
"""

from __future__ import annotations

from enum import IntFlag


class Amenity(IntFlag):
    PS5 = 1
    PC = 2
    VR = 4
    SNOOKER = 8
    AC = 16
    PARKING = 32
    CAFE = 64


AMENITY_LABELS: dict[Amenity, str] = {
    Amenity.PS5: "PS5",
    Amenity.PC: "PC",
    Amenity.VR: "VR",
    Amenity.SNOOKER: "Snooker",
    Amenity.AC: "AC",
    Amenity.PARKING: "Parking",
    Amenity.CAFE: "Cafe",
}


def mask_from_names(names: list[str] | None) -> int:
    if not names:
        return 0
    lookup = {v.lower(): int(k) for k, v in AMENITY_LABELS.items()}
    # aliases
    lookup.update(
        {
            "playstation": int(Amenity.PS5),
            "playstation 5": int(Amenity.PS5),
            "pool": int(Amenity.SNOOKER),
            "billiards": int(Amenity.SNOOKER),
        }
    )
    mask = 0
    for name in names:
        bit = lookup.get(name.strip().lower())
        if bit:
            mask |= bit
    return mask


def names_from_mask(mask: int) -> list[str]:
    return [label for flag, label in AMENITY_LABELS.items() if mask & int(flag)]
