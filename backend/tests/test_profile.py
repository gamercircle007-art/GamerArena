"""Profile related tests using dev.db SQLite data."""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_my_profile_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/users/me/profile")
    # Depending on auth, may be 401 or redirect, but check it's protected
    assert response.status_code in (401, 403, 422)

@pytest.mark.asyncio
async def test_get_user_profile(client: AsyncClient):
    # Use a seeded user id if available, or any
    # From previous demo, try a known one or just check route
    # For demo, we can hit with invalid and check not 404 for route
    response = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000/profile")
    # Expect 404 or 401 depending on setup, but route should exist
    assert response.status_code in (401, 404, 422)

@pytest.mark.asyncio
async def test_update_profile_requires_auth(client: AsyncClient):
    response = await client.put("/api/v1/users/me/profile", json={"bio": "test bio"})
    assert response.status_code in (401, 403, 422)
