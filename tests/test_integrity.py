import pytest
from app.models import Flowchart, PfmeaHeader, PfmeaWorksheetRow, PfmeaTeamMember
from app.services import pfmea_service
from app.services.control_plan_service import (
    create_control_plan_from_pfmea,
    sync_critical_items,
)
from app.schemas.control_plan import ControlPlanCreate
from app.schemas.pfmea import WorksheetRowUpdate
from tests.test_auth import create_account, authenticate


async def project(db, user, status="Draft"):
    fc = Flowchart(
        title="Process",
        plant_id=user.plant_id,
        created_by=user.id,
        owner_id=user.id,
        status="Approved",
    )
    db.add(fc)
    await db.flush()
    doc = PfmeaHeader(
        flowchart_id=fc.id,
        plant_id=user.plant_id,
        owner_id=user.id,
        project_name="Project",
        customer="Customer",
        moc_status=status,
        status=status,
        pfmea_id_number="TEST-PFMEA",
    )
    db.add(doc)
    await db.flush()
    db.add(
        PfmeaTeamMember(
            pfmea_id=doc.id,
            user_id=user.id,
            role_in_team="PFMEA Owner",
            department="Quality",
        )
    )
    row = PfmeaWorksheetRow(
        pfmea_id=doc.id,
        station_operation="Step",
        failure_mode="Failure",
        severity=9,
        occurrence=1,
        detection=7,
        action_priority="H",
    )
    db.add(row)
    await db.commit()
    return doc, row


@pytest.mark.asyncio
async def test_stale_write_and_explicit_deletions(client, db_session):
    user = await create_account(db_session, "PFMEA Owner")
    doc, row = await project(db_session, user)
    await authenticate(client)
    loaded = await client.get(f"/api/v1/pfmea-project/{doc.id}")
    assert loaded.status_code == 200, loaded.text
    version = loaded.json()["lock_version"]
    saved = await client.put(
        f"/api/v1/pfmea-project/{doc.id}/save",
        json={"expected_version": version, "rows": []},
    )
    assert saved.status_code == 200, saved.text
    assert len(saved.json()["worksheet_rows"]) == 1
    stale = await client.put(
        f"/api/v1/pfmea-project/{doc.id}/save",
        json={"expected_version": version, "rows": [], "deleted_row_ids": [row.id]},
    )
    assert stale.status_code == 409, stale.text
    missing = await client.put(
        f"/api/v1/pfmea-project/{doc.id}/worksheet/bulk", json={"rows": []}
    )
    assert missing.status_code == 428
    deleted = await client.put(
        f"/api/v1/pfmea-project/{doc.id}/save",
        json={
            "expected_version": saved.json()["lock_version"],
            "rows": [],
            "deleted_row_ids": [row.id],
        },
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["worksheet_rows"] == []


@pytest.mark.asyncio
async def test_action_text_does_not_complete_and_ap_clears(db_session):
    user = await create_account(db_session, "PFMEA Owner")
    doc, row = await project(db_session, user)
    updated = await pfmea_service.update_worksheet_row(
        db_session,
        doc.id,
        row.id,
        WorksheetRowUpdate(actions_taken="Installed sensor", severity=None),
        user.id,
    )
    assert updated.action_status != "Completed"
    assert updated.action_priority is None


@pytest.mark.asyncio
async def test_plan_sync_identity_and_approved_source(db_session):
    user = await create_account(db_session)
    doc, row = await project(db_session, user)
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        await create_control_plan_from_pfmea(
            db_session, doc.id, user.id, ControlPlanCreate(title="Plan")
        )
    doc.moc_status = "Approved"
    await db_session.flush()
    cp = await create_control_plan_from_pfmea(
        db_session, doc.id, user.id, ControlPlanCreate(title="Plan")
    )
    assert len(cp.items) == 1
    original = cp.items[0].id
    row.failure_mode = "Renamed failure"
    await db_session.flush()
    await sync_critical_items(db_session, cp.id, user.id)
    await db_session.refresh(cp, attribute_names=["items"])
    assert len(cp.items) == 1 and cp.items[0].id == original
    assert cp.items[0].pfmea_worksheet_row_id == row.id


@pytest.mark.asyncio
async def test_owner_cannot_access_other_project(client, db_session):
    owner = await create_account(db_session, "PFMEA Owner", "owner@example.com")
    doc, row = await project(db_session, owner)
    await create_account(db_session, "PFMEA Owner", "other@example.com")
    await authenticate(client, "other@example.com")
    response = await client.get(f"/api/v1/pfmea-project/{doc.id}")
    assert response.status_code in {403, 404}
    listed = await client.get("/api/v1/pfmea-project/")
    assert listed.status_code == 200, listed.text
    assert listed.json() == []
