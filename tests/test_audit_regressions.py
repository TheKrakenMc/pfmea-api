import pytest
from datetime import date
from sqlalchemy import select
from app.models import AuditLog, DocumentVersion, Plant, Product, ProductParameter
from tests.test_auth import create_account, authenticate
from tests.test_integrity import project
from app.services.control_plan_service import create_control_plan_from_pfmea
from app.schemas.control_plan import ControlPlanCreate


@pytest.mark.asyncio
async def test_action_validation_invalidation_and_atomic_audit(client, db_session):
    user = await create_account(db_session, "PFMEA Owner")
    doc, row = await project(db_session, user)
    await authenticate(client)
    invalid = await client.post(
        f"/api/v1/pfmea-project/{doc.id}/worksheet/{row.id}/confirm-action",
        headers={"If-Match": "1"},
    )
    assert invalid.status_code == 400, invalid.text
    row.actions_taken = "Sensor installed; validation report QA-001"
    row.responsible_person_id = user.id
    row.completion_date = date.today()
    row.new_severity, row.new_occurrence, row.new_detection = 9, 1, 7
    await db_session.commit()
    confirmed = await client.post(
        f"/api/v1/pfmea-project/{doc.id}/worksheet/{row.id}/confirm-action",
        headers={"If-Match": "1"},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["action_status"] == "Completed"
    assert confirmed.json()["validated_by"] == user.id
    saved = await client.put(
        f"/api/v1/pfmea-project/{doc.id}/save",
        json={
            "expected_version": 2,
            "rows": [{"id": row.id, "actions_taken": "Changed evidence"}],
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["worksheet_rows"][0]["validated_by"] is None
    logs = (
        await db_session.scalars(
            select(AuditLog).where(AuditLog.performed_by == user.id)
        )
    ).all()
    assert any(log.action == "ACTION_CONFIRMED" for log in logs)
    assert any(
        log.field_name == "actions_taken"
        and log.old_value
        and "QA-001" in log.old_value
        for log in logs
    )
    assert not any(
        log.field_name in {"password_hash", "refresh_hash", "csrf_token", "otp_code"}
        for log in logs
    )


@pytest.mark.asyncio
async def test_control_reopen_preserves_snapshot_and_deleted_source(client, db_session):
    user = await create_account(db_session, "PFMEA Owner")
    doc, row = await project(db_session, user, "Approved")
    cp = await create_control_plan_from_pfmea(
        db_session, doc.id, user.id, ControlPlanCreate(title="Plan")
    )
    cp.status = "Approved"
    await db_session.commit()
    await authenticate(client)
    denied = await client.put(
        f"/api/v1/control-plans/items/{cp.items[0].id}",
        headers={"If-Match": "1"},
        json={"characteristic": "Edited"},
    )
    assert denied.status_code == 403
    reopened = await client.post(
        f"/api/v1/control-plans/{cp.id}/restore",
        headers={"If-Match": "1"},
        json={"reason": "Review changed source"},
    )
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["status"] == "Draft"
    versions = (
        await db_session.scalars(
            select(DocumentVersion).where(
                DocumentVersion.document_id == cp.id,
                DocumentVersion.document_type == "control_plan",
            )
        )
    ).all()
    assert versions[0].snapshot_data["status"] == "Approved"
    restored = await client.post(
        f"/api/v1/pfmea-project/{doc.id}/restore", headers={"If-Match": "1"}
    )
    assert restored.status_code == 200, restored.text
    deleted = await client.put(
        f"/api/v1/pfmea-project/{doc.id}/save",
        json={"expected_version": 2, "deleted_row_ids": [row.id]},
    )
    assert deleted.status_code == 200, deleted.text
    await db_session.refresh(cp, attribute_names=["items"])
    assert len(cp.items) == 1
    assert cp.items[0].pfmea_worksheet_row_id is None
    assert cp.items[0].needs_review


@pytest.mark.asyncio
async def test_parameter_ids_and_image_upload_are_isolated(
    client, db_session, tmp_path, monkeypatch
):
    await create_account(db_session, "PFMEA Owner")
    other = Plant(name="Other", code="OTHER", is_active=True)
    db_session.add(other)
    await db_session.flush()
    product = Product(part_number="Other product", plant_id=other.id, status="Draft")
    db_session.add(product)
    await db_session.flush()
    parameter = ProductParameter(product_id=product.id, name="Secret parameter")
    db_session.add(parameter)
    await db_session.commit()
    await authenticate(client)
    assert (
        await client.put(
            f"/api/v1/products/parameters/{parameter.id}", json={"name": "Attack"}
        )
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/products/{product.id}/parameters")
    ).status_code == 404
    from app.api.v1.endpoints import product as endpoint

    monkeypatch.setattr(endpoint, "UPLOAD_ROOT", tmp_path)
    bad = await client.post(
        "/api/v1/products/upload-image",
        files={
            "file": ("../../attack.html", b"<script>alert(1)</script>", "image/png")
        },
    )
    assert bad.status_code == 415, bad.text
    uploaded = await client.post(
        "/api/v1/products/upload-image",
        files={
            "file": ("../../attack.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")
        },
    )
    assert uploaded.status_code == 200, uploaded.text
    assert "attack" not in uploaded.json()["filename"]
    assert len(list(tmp_path.rglob("*.png"))) == 1
    assert (await client.get(uploaded.json()["path"])).status_code == 200
    await client.post("/api/v1/auth/logout")
    assert (await client.get(uploaded.json()["path"])).status_code == 401


@pytest.mark.asyncio
async def test_multi_plant_assignment_revoke_sessions(client, db_session):
    await create_account(db_session)
    user = await create_account(db_session, "PFMEA Owner", "owner@example.com")
    other = Plant(name="Second", code="SECOND", is_active=True)
    db_session.add(other)
    await db_session.commit()
    await authenticate(client)
    assigned = await client.put(
        f"/api/v1/users/{user.id}/plants",
        json={"plant_ids": [user.plant_id, other.id], "primary_plant_id": other.id},
    )
    assert assigned.status_code == 200, assigned.text
    await client.post("/api/v1/auth/logout")
    logged = await authenticate(client, "owner@example.com")
    assert set(logged.json()["user"]["plant_ids"]) == {user.plant_id, other.id}
    assert (
        await client.get(
            "/api/v1/pfmea-project/", headers={"X-Plant-Id": str(other.id)}
        )
    ).status_code == 200
