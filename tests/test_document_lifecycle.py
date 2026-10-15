import pytest
from datetime import datetime, timedelta, timezone
from app.models import UserOTP, Technology
from app.api.v1.endpoints.auth import recovery_digest
from app.core.security import create_verification_token
from tests.test_auth import create_account, authenticate


@pytest.mark.asyncio
async def test_product_revision_and_atomic_parameter_conflict(client, db_session):
    await create_account(db_session)
    tech = Technology(name="Synthetic operation", code="SYNTH")
    db_session.add(tech)
    await db_session.commit()
    await authenticate(client)
    created = await client.post("/api/v1/products/", json={"part_number": "REV-01"})
    assert created.status_code == 201, created.text
    product = created.json()
    assert product["status"] == "Draft"
    path = "/api/v1/products/" + str(product["id"])
    saved = await client.put(
        path, headers={"If-Match": "1"}, json={"description": "Updated"}
    )
    assert saved.status_code == 200, saved.text
    stale = await client.put(
        path, headers={"If-Match": "1"}, json={"description": "Obsolete"}
    )
    assert stale.status_code == 409, stale.text
    review = await client.put(
        path + "/status", headers={"If-Match": "2"}, json={"status": "In Review"}
    )
    assert review.status_code == 200, review.text
    released = await client.put(
        path + "/status", headers={"If-Match": "3"}, json={"status": "Released"}
    )
    assert released.status_code == 200, released.text
    assert (
        await client.put(
            path, headers={"If-Match": "4"}, json={"description": "Forbidden"}
        )
    ).status_code == 403
    revision = await client.post(
        path + "/revisions",
        headers={"If-Match": "4"},
        json={
            "change_reason": "New controlled engineering revision",
            "engineering_level": "B",
        },
    )
    assert revision.status_code == 201, revision.text
    assert revision.json()["snapshot_data"]["status"] == "Released"
    assert revision.json()["revision_number"] == 1
    current = (await client.get(path)).json()
    assert (
        current["version"] == 2
        and current["status"] == "Draft"
        and current["lock_version"] == 5
    )
    invalid = await client.put(
        path + "/parameters/bulk",
        json={
            "expected_version": 5,
            "rows": [{"name": "Invalid unit", "measurement_unit_id": 99999}],
        },
    )
    assert invalid.status_code == 400, invalid.text
    current = (await client.get(path)).json()
    assert current["lock_version"] == 5
    bulk = await client.put(
        path + "/parameters/bulk",
        json={
            "expected_version": 5,
            "rows": [
                {"name": "Temperature", "technology_id": tech.id},
                {"name": "Pressure", "technology_id": tech.id},
            ],
        },
    )
    assert bulk.status_code == 200, bulk.text
    assert len(bulk.json()["parameters"]) == 2
    assert (
        await client.put(
            path + "/parameters/bulk", json={"expected_version": 5, "rows": []}
        )
    ).status_code == 409


@pytest.mark.asyncio
async def test_diagram_creation_preserves_substeps_and_requires_approval(
    client, db_session
):
    await create_account(db_session)
    await authenticate(client)
    product = (
        await client.post("/api/v1/products/", json={"part_number": "FLOW-01"})
    ).json()
    payload = {"product_id": product["id"], "title": "Substeps", "status": "Approved"}
    assert (await client.post("/api/v1/flowcharts/", json=payload)).status_code == 400
    payload.update(
        status="Draft",
        steps=[
            {"step_number": 10, "sub_step": 0, "product_characteristics": "Dimension"},
            {"step_number": 10, "sub_step": 1, "process_characteristics": "Pressure"},
        ],
    )
    created = await client.post("/api/v1/flowcharts/", json=payload)
    assert created.status_code == 201, created.text
    diagram = created.json()
    assert [s["sub_step"] for s in diagram["steps"]] == [0, 1]
    assert diagram["steps"][0]["product_characteristics"] == "Dimension"
    rejected = await client.post(
        "/api/v1/pfmea-project/",
        json={
            "flowchart_id": diagram["id"],
            "project_name": "Unapproved",
            "customer": "Synthetic",
        },
    )
    assert rejected.status_code == 400, rejected.text


@pytest.mark.asyncio
async def test_purpose_tokens_and_password_reset_revoke_sessions(client, db_session):
    user = await create_account(db_session)
    await authenticate(client)
    code = UserOTP(
        user_id=user.id,
        otp_code=recovery_digest("123456"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        is_used=False,
    )
    db_session.add(code)
    await db_session.commit()
    reset = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": user.email,
            "otp_code": "123456",
            "new_password": "ReplacementPassword123!",
        },
    )
    assert reset.status_code == 200, reset.text
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    repeated = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": user.email,
            "otp_code": "123456",
            "new_password": "AnotherPassword123!",
        },
    )
    assert repeated.status_code == 400
    user.is_verified = False
    await db_session.commit()
    verification = create_verification_token(user.email)
    client.cookies.clear()
    client.cookies.set("access_token", verification)
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    client.cookies.clear()
    verified = await client.post(
        "/api/v1/auth/verify-email", json={"token": verification}
    )
    assert verified.status_code == 200, verified.text
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": verification})
    ).status_code == 400


@pytest.mark.asyncio
async def test_create_control_plan_from_approved_pfmea_over_http(client,db_session):
    from tests.test_integrity import project
    user=await create_account(db_session)
    doc,row=await project(db_session,user,"Approved")
    await authenticate(client)
    created=await client.post(f"/api/v1/control-plans/project/{doc.id}",headers={"If-Match":"1"},json={"title":"Approved source plan"})
    assert created.status_code==201,created.text
    assert created.json()["items"][0]["pfmea_worksheet_row_id"]==row.id
    loaded=await client.get(f"/api/v1/pfmea-project/{doc.id}")
    assert loaded.json()["moc_status"]=="Approved"
    assert (await client.put(f"/api/v1/pfmea-project/{doc.id}/save",json={"expected_version":2,"rows":[]})).status_code==403
