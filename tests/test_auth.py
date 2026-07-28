import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_otp import UserOTP
from app.models.role import Role
from app.core.hashing import hash_password
from app.services.seed import seed_db

@pytest.mark.asyncio
async def test_complete_security_flow(client: AsyncClient, db_session: AsyncSession):
    """
    Test the full security flow:
    1. Defensive DB seeding.
    2. Two-phase authentication (Phase 1: Credentials -> Phase 2: OTP).
    3. Token-based session verification (/auth/me).
    4. Silent token refresh (/auth/refresh).
    5. Logout cookie clearing (/auth/logout).
    """
    # 1. Seed database to populate roles and default plant
    await seed_db(db_session)

    # Fetch seeded administrator to know credentials
    stmt = select(User).where(User.email == "antonio.tlaque@adlerpelzer.com")
    res = await db_session.execute(stmt)
    admin = res.scalars().first()
    assert admin is not None
    assert admin.full_name == "Antonio Tlaque"

    # 2. Phase 1 Login: credentials validation
    # Incorrect credentials should fail
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "antonio.tlaque@adlerpelzer.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

    # Correct credentials should trigger OTP creation and email notification
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "antonio.tlaque@adlerpelzer.com", "password": "APGPuebla2026!"}
    )
    assert response.status_code == 200
    assert response.json()["otp_required"] is True

    # Retrieve generated OTP from DB for testing
    stmt_otp = select(UserOTP).where(UserOTP.user_id == admin.id).order_by(UserOTP.created_at.desc())
    res_otp = await db_session.execute(stmt_otp)
    db_otp = res_otp.scalars().first()
    assert db_otp is not None
    assert db_otp.is_used is False

    # 3. Phase 2 Login: verify OTP and check cookies
    # Incorrect OTP should fail
    response_otp = await client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "antonio.tlaque@adlerpelzer.com", "otp_code": "000000"}
    )
    assert response_otp.status_code == 400

    # Correct OTP should succeed and set cookies
    response_otp = await client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "antonio.tlaque@adlerpelzer.com", "otp_code": db_otp.otp_code}
    )
    assert response_otp.status_code == 200
    assert "access_token" in response_otp.cookies
    assert "refresh_token" in response_otp.cookies

    # Verify OTP was marked as used
    await db_session.refresh(db_otp)
    assert db_otp.is_used is True

    # Set client cookies to verify /me session endpoint
    client.cookies.set("access_token", response_otp.cookies["access_token"])
    client.cookies.set("refresh_token", response_otp.cookies["refresh_token"])

    # 4. Check session details
    response_me = await client.get("/api/v1/auth/me")
    assert response_me.status_code == 200
    assert response_me.json()["email"] == "antonio.tlaque@adlerpelzer.com"
    assert response_me.json()["role_name"] == "Administrator"

    # 5. Silent Token Refresh
    response_refresh = await client.post("/api/v1/auth/refresh")
    assert response_refresh.status_code == 200
    assert "access_token" in response_refresh.cookies
    assert "refresh_token" in response_refresh.cookies

    # 6. Logout cookie clearing
    response_logout = await client.post("/api/v1/auth/logout")
    assert response_logout.status_code == 200
    # Cookies should be empty or deleted
    assert client.cookies.get("access_token") is None or "max-age=0" in response_logout.headers.get("set-cookie", "")

@pytest.mark.asyncio
async def test_user_management_and_archiving(client: AsyncClient, db_session: AsyncSession):
    """
    Test user registration, role updates, deactivation and visual archiving.
    """
    # 1. Seed database to populate roles and default plant
    await seed_db(db_session)

    # 2. Register new user (Public registration)
    reg_response = await client.post(
        "/api/v1/users/register",
        json={
            "full_name": "Juan Perez",
            "email": "juan.perez@adlerpelzer.com",
            "password": "JuanPassword123!",
            "employment_position": "Quality Engineer"
        }
    )
    assert reg_response.status_code == 200
    new_user_data = reg_response.json()
    assert new_user_data["role_name"] == "Viewer"  # Default role Viewer
    assert new_user_data["is_active"] is True

    # 3. Access users list without Admin should fail (401/403)
    list_response = await client.get("/api/v1/users/")
    assert list_response.status_code == 401

    # Login as Administrator to perform Admin functions
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "antonio.tlaque@adlerpelzer.com", "password": "APGPuebla2026!"}
    )
    stmt_otp = select(UserOTP).order_by(UserOTP.created_at.desc()).limit(1)
    res_otp = await db_session.execute(stmt_otp)
    otp = res_otp.scalars().first()
    
    verify_res = await client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "antonio.tlaque@adlerpelzer.com", "otp_code": otp.otp_code}
    )
    client.cookies.set("access_token", verify_res.cookies["access_token"])
    client.cookies.set("refresh_token", verify_res.cookies["refresh_token"])

    # 4. Access users list as Admin should succeed
    list_response = await client.get("/api/v1/users/")
    assert list_response.status_code == 200
    users = list_response.json()
    assert len(users) >= 2  # Admin + Juan Perez

    # Find registered user ID
    juan_id = new_user_data["id"]

    # 5. Admin updates User role to PFMEA Owner
    role_response = await client.put(
        f"/api/v1/users/{juan_id}/role",
        json={"role_name": "PFMEA Owner"}
    )
    assert role_response.status_code == 200
    assert role_response.json()["role_name"] == "PFMEA Owner"

    # 6. Admin deactivates/inactivates User (Visual Archiving)
    status_response = await client.put(
        f"/api/v1/users/{juan_id}/status",
        json={"is_active": False}
    )
    assert status_response.status_code == 200
    updated_user = status_response.json()
    assert updated_user["is_active"] is False
    assert updated_user["full_name"] == "ARCHIVED Juan Perez"  # TISAX visual archiving constraint

    # 7. Reactivate User
    reactivate_response = await client.put(
        f"/api/v1/users/{juan_id}/status",
        json={"is_active": True}
    )
    assert reactivate_response.status_code == 200
    reactivated_user = reactivate_response.json()
    assert reactivated_user["is_active"] is True
    assert reactivated_user["full_name"] == "Juan Perez"  # Strip ARCHIVED prefix
