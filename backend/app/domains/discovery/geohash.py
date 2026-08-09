"""Inline geohash (precision 6 ≈ 1.2 km) — no heavy dependency."""

from __future__ import annotations

_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encode(lat: float, lng: float, precision: int = 6) -> str:
    lat_min, lat_max = -90.0, 90.0
    lng_min, lng_max = -180.0, 180.0
    bits: list[int] = []
    even = True
    while len(bits) < precision * 5:
        if even:
            mid = (lng_min + lng_max) / 2
            if lng >= mid:
                bits.append(1)
                lng_min = mid
            else:
                bits.append(0)
                lng_max = mid
        else:
            mid = (lat_min + lat_max) / 2
            if lat >= mid:
                bits.append(1)
                lat_min = mid
            else:
                bits.append(0)
                lat_max = mid
        even = not even
    chars: list[str] = []
    for i in range(0, len(bits), 5):
        idx = 0
        for b in bits[i : i + 5]:
            idx = (idx << 1) | b
        chars.append(_BASE32[idx])
    return "".join(chars)
