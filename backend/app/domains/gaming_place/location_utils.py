"""Extract city/state/country and open status from gaming place rows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.domains.gaming_place.models import GamingPlace


def _components(raw: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    comps = raw.get("address_components")
    return comps if isinstance(comps, list) else []


def _component(components: list[dict[str, Any]], type_name: str) -> str | None:
    for comp in components:
        types = comp.get("types") or []
        if type_name in types:
            return comp.get("long_name") or comp.get("short_name")
    return None


def extract_locality(place: GamingPlace) -> tuple[str | None, str | None, str | None]:
    raw = place.raw_data if isinstance(place.raw_data, dict) else None
    components = _components(raw)
    city = _component(components, "locality") or _component(components, "administrative_area_level_2")
    state = _component(components, "administrative_area_level_1")
    country = _component(components, "country")
    if city or state or country:
        return city, state, country
    if place.address:
        parts = [p.strip() for p in place.address.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[-3] if len(parts) >= 3 else parts[-2], parts[-2], parts[-1]
    return None, None, None


def extract_images(place: GamingPlace) -> list[str]:
    from app.domains.gaming_place.mappers import resolve_media_url

    images: list[str] = []
    if place.image_url:
        resolved = resolve_media_url(place.image_url)
        if resolved:
            images.append(resolved)
    if isinstance(place.photos, list):
        for photo in place.photos[:5]:
            if isinstance(photo, str):
                resolved = resolve_media_url(photo)
                if resolved:
                    images.append(resolved)
            elif isinstance(photo, dict):
                url = photo.get("url") or photo.get("photo_url")
                resolved = resolve_media_url(url) if isinstance(url, str) else None
                if resolved:
                    images.append(resolved)
    return images


def is_open_now(place: GamingPlace) -> bool:
    if (place.business_status or "").upper() not in {"", "OPERATIONAL"}:
        return False
    hours = place.opening_hours
    if not isinstance(hours, dict):
        return True
    if hours.get("open_now") is False:
        return False
    weekday = datetime.now(UTC).weekday()
    periods = hours.get("periods")
    if not isinstance(periods, list) or not periods:
        return True
    for period in periods:
        if not isinstance(period, dict):
            continue
        open_info = period.get("open") or {}
        if open_info.get("day") == weekday:
            return True
    return True