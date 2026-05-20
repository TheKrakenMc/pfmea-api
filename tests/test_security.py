import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rbac_viewer_forbidden(client: AsyncClient, test_user, valid_viewer_token: str):
    """Verify that a user with Viewer role (2) gets 403 when trying to POST to /flowcharts/."""
    # "PFMEA Owner" role in mock is string 'PFMEA Owner'.
    # Actually, in conftest we set the viewer token role_id="2".
    # And RoleChecker expects `['PFMEA Owner']`.
    # It will compare "2" not in `['PFMEA Owner']` -> 403 Forbidden.
    client.cookies.set("access_token", valid_viewer_token)
    response = await client.post(
        "/api/v1/flowcharts/",
        json={"product_id": 1, "name": "Test Flowchart"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Operation not permitted"

@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient, test_user):
    """Test that the auth login endpoint blocks requests after limit (5/minute)."""
    # Send 6 rapid requests to /api/v1/auth/login. Limit is 5/min.
    # The first 5 might fail due to bad credentials or succeed, but the 6th should be 429.
    
    responses = []
    for _ in range(6):
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com"}
        )
        responses.append(res.status_code)
    
    # At least the last response must be 429
    assert 429 in responses
    assert responses[-1] == 429
