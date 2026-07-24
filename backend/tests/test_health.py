"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    # APP_NAME default is gamer-circle (legacy name was paythan)
    assert data["service"] in ("gamer-circle", "paythan", "GamerCircle")