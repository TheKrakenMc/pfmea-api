import pytest
from tests.test_auth import create_account, authenticate


@pytest.mark.asyncio
async def test_rbac_viewer_forbidden(client, db_session):
    await create_account(db_session, "Viewer")
    await authenticate(client)
    response = await client.post(
        "/api/v1/flowcharts/", json={"product_id": 1, "title": "Test"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_rate_limiting(client):
    responses = [
        await client.post(
            "/api/v1/auth/login",
            json={"email": "none@example.com", "password": "wrong"},
        )
        for _ in range(6)
    ]
    assert responses[-1].status_code == 429


@pytest.mark.asyncio
async def test_all_private_routes_require_auth(client):
    from app.main import app

    public = {
        "/api/v1/auth/csrf",
        "/api/v1/auth/login",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/refresh",
        "/api/v1/health",
        "/api/v1/readiness",
    }
    for route, operations in app.openapi()["paths"].items():
        if not route.startswith("/api/v1") or route in public:
            continue
        import re

        path = re.sub(r"\{[^}]+\}", "1", route)
        for method in operations:
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            response = await client.request(method, path, json={})
            assert response.status_code == 401, (
                method,
                path,
                response.status_code,
                response.text,
            )


@pytest.mark.asyncio
async def test_viewer_cannot_write_any_private_endpoint(client, db_session):
    import re
    from tests.test_auth import create_account, authenticate
    from app.main import app

    await create_account(db_session, "Viewer")
    await authenticate(client)
    for path, operations in app.openapi()["paths"].items():
        if not path.startswith("/api/v1/") or "/auth/" in path:
            continue
        target = re.sub(r"\{[^}]+\}", "1", path)
        for method in operations:
            if method not in {"post", "put", "patch", "delete"}:
                continue
            response = await client.request(method.upper(), target, json={})
            assert response.status_code == 403, (
                method,
                path,
                response.status_code,
                response.text,
            )
