import pytest
from sqlalchemy import select
from app.models import User, Role, Plant
from app.models.auth_session import UserPlant, AuthSession
from app.core.hashing import hash_password
from app.services.seed import seed_db


async def create_account(db, role_name="Administrator", email="admin@example.com"):
    await seed_db(db)
    role = (await db.scalars(select(Role).where(Role.name == role_name))).one()
    plant = (await db.scalars(select(Plant))).first()
    user = User(
        email=email,
        full_name="Test User",
        password_hash=hash_password("TestPassword123!"),
        role_id=role.id,
        plant_id=plant.id,
        is_active=True,
        is_verified=True,
        must_change_password=False,
    )
    db.add(user)
    await db.flush()
    db.add(UserPlant(user_id=user.id, plant_id=plant.id))
    await db.commit()
    return user


async def authenticate(client, email="admin@example.com"):
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "TestPassword123!"}
    )
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return response


@pytest.mark.asyncio
async def test_complete_security_flow(client, db_session):
    user = await create_account(db_session)
    bad = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "wrong"}
    )
    assert bad.status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/verify-otp", json={"email": user.email, "otp_code": "000000"}
        )
    ).status_code == 404
    response = await authenticate(client)
    assert "HttpOnly" in response.headers.get("set-cookie", "")
    assert (await client.get("/api/v1/auth/me")).status_code == 200
    old_refresh = client.cookies.get("refresh_token")
    assert (await client.post("/api/v1/auth/refresh")).status_code == 200
    assert client.cookies.get("refresh_token") != old_refresh
    old_access = client.cookies.get("access_token")
    assert (await client.post("/api/v1/auth/logout")).status_code == 200
    client.cookies.set("access_token", old_access)
    assert (await client.get("/api/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_session(client, db_session):
    await create_account(db_session)
    await authenticate(client)
    token = client.cookies.get("refresh_token")
    assert (await client.post("/api/v1/auth/refresh")).status_code == 200
    client.cookies.clear()
    client.cookies.set("refresh_token", token)
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401
    sessions = (await db_session.scalars(select(AuthSession))).all()
    await db_session.refresh(sessions[0])
    assert sessions[0].revoked


@pytest.mark.asyncio
async def test_csrf_origin_and_plant_validation(client, db_session):
    await create_account(db_session, "Viewer")
    await authenticate(client)
    assert (
        await client.post("/api/v1/control-plans/project/1", json={"title": "x"})
    ).status_code == 403
    client.headers.pop("X-CSRF-Token")
    assert (await client.post("/api/v1/auth/logout")).status_code == 403
    assert (
        await client.get("/api/v1/pfmea-project/", headers={"X-Plant-Id": "999999"})
    ).status_code == 403
    assert (
        await client.post(
            "/api/v1/auth/login",
            headers={"Origin": "https://evil.example"},
            json={"email": "a@example.com", "password": "x"},
        )
    ).status_code == 403


@pytest.mark.asyncio
async def test_user_management_and_archiving(client, db_session):
    await create_account(db_session)
    assert (
        await client.post(
            "/api/v1/users/register",
            json={
                "full_name": "Juan Perez",
                "email": "juan@example.com",
                "password": "JuanPassword123!",
            },
        )
    ).status_code == 401
    await authenticate(client)
    response = await client.post(
        "/api/v1/users/register",
        json={
            "full_name": "Juan Perez",
            "email": "juan@example.com",
            "password": "JuanPassword123!",
        },
    )
    assert response.status_code == 200, response.text
    uid = response.json()["id"]
    assert (
        await client.put(f"/api/v1/users/{uid}/role", json={"role_name": "PFMEA Owner"})
    ).status_code == 200
    inactive = await client.put(
        f"/api/v1/users/{uid}/status", json={"is_active": False}
    )
    assert inactive.status_code == 200
    assert inactive.json()["full_name"] == "ARCHIVED Juan Perez"
    active = await client.put(f"/api/v1/users/{uid}/status", json={"is_active": True})
    assert active.status_code == 200
    assert active.json()["full_name"] == "Juan Perez"


@pytest.mark.asyncio
async def test_legacy_token_and_admin_routes_removed(client, db_session):
    from app.core.security import create_access_token

    user = await create_account(db_session)
    client.cookies.set("access_token", create_access_token(user.id, user.role_id))
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    assert (await client.get("/api/v1/migrate_now")).status_code == 404
    assert (await client.get("/api/v1/instruction/")).status_code == 404
