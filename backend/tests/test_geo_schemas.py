"""Geo schema tests."""

from uuid import uuid4

from app.domains.geo.schemas import NearbyParlorResponse


def test_nearby_parlor_includes_coordinates() -> None:
    row = NearbyParlorResponse(
        id=uuid4(),
        name="Test Arena",
        game_types=["BGMI"],
        is_verified=True,
        follower_count=10,
        distance_meters=500.0,
        lat=28.63,
        lng=77.21,
    )
    assert row.lat == 28.63
    assert row.lng == 77.21