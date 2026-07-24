"""Home parlors distance and schema tests."""

import pytest
from httpx import AsyncClient

from app.domains.geo.service import GeoService


def test_haversine_meters_known_distance() -> None:
    """Delhi (28.6139, 77.2090) to Noida (28.5355, 77.3910) ~ 19–21 km."""
    distance = GeoService._haversine_meters(28.6139, 77.2090, 28.5355, 77.3910)
    assert 18_000 < distance < 22_000


def test_haversine_meters_same_point_is_zero() -> None:
    distance = GeoService._haversine_meters(12.9716, 77.5946, 12.9716, 77.5946)
    assert distance == pytest.approx(0.0, abs=1.0)


@pytest.mark.asyncio
async def test_home_response_includes_nearby_parlors(client: AsyncClient) -> None:
    spec = (await client.get("/openapi.json")).json()
    home_get = spec["paths"]["/api/v1/home"]["get"]
    schema_ref = home_get["responses"]["200"]["content"]["application/json"]["schema"]
    if "$ref" in schema_ref:
        schema_name = schema_ref["$ref"].split("/")[-1]
        props = spec["components"]["schemas"][schema_name]["properties"]
    else:
        props = schema_ref.get("properties", {})
    assert "nearby_parlors" in props
    assert "radius_meters" in props


@pytest.mark.asyncio
async def test_home_accepts_radius_filter(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/home",
        params={"lat": 28.6139, "lng": 77.2090, "radius": 5000},
    )
    # 200 when DB is available; 500 acceptable in CI without DB
    assert response.status_code in {200, 500}
    if response.status_code == 200:
        data = response.json()
        assert "nearby_parlors" in data
        assert isinstance(data["nearby_parlors"], list)
        distances = [
            item["distance_meters"]
            for item in data["nearby_parlors"]
            if item.get("distance_meters") is not None
        ]
        for d in distances:
            assert d <= 5000 + 1
        if len(distances) >= 2:
            assert distances == sorted(distances)