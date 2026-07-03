"""Social API route smoke tests (no DB required for auth-gated endpoints)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_feed_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/feed")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_geo_nearby_parlors_route_registered(client: AsyncClient) -> None:
    spec = (await client.get("/openapi.json")).json()
    path = spec["paths"].get("/api/v1/geo/nearby-parlors")
    assert path is not None
    assert "get" in path


@pytest.mark.asyncio
async def test_payments_order_local_dev(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/payments/razorpay/order",
        json={"amount_paise": 19900, "receipt": "test_rcpt"},
    )
    # Local env returns dev order; production without keys returns 503
    assert response.status_code in {200, 503}


@pytest.mark.asyncio
async def test_razorpay_config_public(client: AsyncClient) -> None:
    response = await client.get("/api/v1/payments/razorpay/config")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "key_id" in data


@pytest.mark.asyncio
async def test_booking_payment_order_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/payments/razorpay/bookings/00000000-0000-0000-0000-000000000001/order",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_stats_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_openapi_lists_social_tags(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    tags = {t["name"] for t in response.json()["tags"]}
    assert "Geo" in tags
    assert "Feed" in tags
    assert "Payments" in tags