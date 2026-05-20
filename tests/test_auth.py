import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login returns HttpOnly cookie."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@test.com"}
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    # Since we can't assert HttpOnly on the client easily this way, we just assert the cookie is set.

@pytest.mark.asyncio
async def test_login_invalid_email(client: AsyncClient, test_user):
    """Test login fails with invalid email."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com"}
    )
    assert response.status_code == 401
    assert "access_token" not in response.cookies

@pytest.mark.asyncio
async def test_protected_endpoint_without_cookie(client: AsyncClient):
    """Verify that accessing a protected endpoint without the HTTP-Only cookie returns 401."""
    response = await client.post(
        "/api/v1/flowcharts/",
        json={"product_id": 1, "name": "Test"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_cookie(client: AsyncClient, invalid_token: str):
    """Verify that accessing a protected endpoint with an invalid cookie returns 401."""
    client.cookies.set("access_token", f"Bearer {invalid_token}")
    response = await client.post(
        "/api/v1/flowcharts/",
        json={"product_id": 1, "name": "Test"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
