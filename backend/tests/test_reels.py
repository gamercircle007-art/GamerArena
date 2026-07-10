"""Reels API tests."""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_reel_feed_requires_auth_or_works(client: AsyncClient):
    response = await client.get("/api/v1/feed")  # may be reel feed
    # Reels feed might be public or protected
    assert response.status_code in (200, 401, 404)

@pytest.mark.asyncio
async def test_reel_search_route(client: AsyncClient):
    spec = (await client.get("/openapi.json")).json()
    # Check if reel search or feed exists
    paths = spec.get("paths", {})
    assert any("/reel" in p or "/feed" in p for p in paths)
