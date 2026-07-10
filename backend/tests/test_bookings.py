"""Bookings tests."""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_my_bookings_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/users/me/gaming-bookings")
    assert response.status_code in (401, 403, 422)

@pytest.mark.asyncio
async def test_booking_routes_registered(client: AsyncClient):
    spec = (await client.get("/openapi.json")).json()
    paths = spec.get("paths", {})
    assert any("gaming-bookings" in p or "bookings" in p for p in paths)
