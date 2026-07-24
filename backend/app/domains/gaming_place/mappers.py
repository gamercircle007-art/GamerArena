"""Map gaming place rows to API-facing parlor shapes."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.core.config import get_settings
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension


@dataclass
class GamingPlaceView:
    """Parlor-compatible view backed by ``gaming_places`` + optional extension."""

    id: UUID
    name: str
    description: str | None
    logo_url: str | None
    address: str | None
    game_types: list[str]
    is_verified: bool
    follower_count: int
    post_count: int
    owner_id: UUID | None
    rating: float | None
    phone: str | None
    website: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    is_deleted: bool = False


def resolve_media_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    base = get_settings().gaming_places_media_base_url.rstrip("/")
    return f"{base}{url}" if base else url


def derive_game_types(place: GamingPlace) -> list[str]:
    if place.primary_type:
        return [place.primary_type.replace("_", " ").upper()]
    if isinstance(place.types, list) and place.types:
        return [str(t).replace("_", " ").upper() for t in place.types[:5]]
    return ["GAMING"]


def is_operational(place: GamingPlace) -> bool:
    return (place.business_status or "").upper() == "OPERATIONAL"


def to_view(
    place: GamingPlace,
    extension: GamingPlaceExtension | None = None,
) -> GamingPlaceView:
    ext = extension
    return GamingPlaceView(
        id=place.id,
        name=place.name,
        description=None,
        logo_url=resolve_media_url(place.image_url),
        address=place.address,
        game_types=derive_game_types(place),
        is_verified=ext.is_verified if ext else is_operational(place),
        follower_count=ext.follower_count if ext else 0,
        post_count=ext.post_count if ext else 0,
        owner_id=ext.owner_id if ext else None,
        rating=place.rating,
        phone=place.phone,
        website=place.website,
        latitude=place.latitude,
        longitude=place.longitude,
        created_at=place.created_at,
        updated_at=place.updated_at,
        is_active=ext.is_active if ext else True,
        is_deleted=ext.is_deleted if ext else False,
    )


def utc_now() -> datetime:
    return datetime.now(UTC)