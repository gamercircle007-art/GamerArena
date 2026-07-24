"""Expanded auth tests."""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code in (401, 403, 422)

@pytest.mark.asyncio
async def test_login_endpoints_registered(client: AsyncClient):
    spec = (await client.get("/openapi.json")).json()
    paths = spec.get("paths", {})
    auth_paths = [p for p in paths if "auth" in p or "login" in p or "otp" in p]
    assert len(auth_paths) > 0
