"""Synthetic local QA server; never connects to the configured project database."""

import os

os.environ["ENVIRONMENT"] = "testing"
os.environ["RESEND_API_KEY"] = ""
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5174,http://127.0.0.1:5174"
os.environ["BACKEND_CORS_ORIGINS"] = "http://localhost:5174,http://127.0.0.1:5174"
from datetime import date
import asyncio
import uvicorn
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
import app.main as main_module
from app.core.db import get_db
from app.models import (
    Base,
    User,
    Role,
    Plant,
    Customer,
    Product,
    Technology,
    Flowchart,
    FlowchartStep,
    PfmeaHeader,
    PfmeaTeamMember,
    PfmeaWorksheetRow,
    ControlPlan,
    ControlPlanItem,
)
from app.models.auth_session import UserPlant
from app.core.hashing import hash_password
from app.services.seed import seed_db
from sqlalchemy import select

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
Sessions = async_sessionmaker(engine, expire_on_commit=False)


async def isolated_db():
    async with Sessions() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise


app.dependency_overrides[get_db] = isolated_db
main_module.engine = engine


async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with Sessions() as db:
        await seed_db(db)
        plant = (await db.scalars(select(Plant))).first()
        role = (
            await db.scalars(select(Role).where(Role.name == "Administrator"))
        ).one()
        user = User(
            email="audit@example.com",
            full_name="Auditor sintético",
            password_hash=hash_password("AuditPassword123!"),
            plant_id=plant.id,
            role_id=role.id,
            is_active=True,
            is_verified=True,
            must_change_password=False,
        )
        db.add(user)
        await db.flush()
        db.add(UserPlant(user_id=user.id, plant_id=plant.id))
        customer = Customer(
            company_name="Cliente sintético",
            customer_code="QA-CUST",
            plant_id=plant.id,
            is_active=True,
        )
        technology = Technology(name="Inspección", code="QA-01", is_active=True)
        db.add_all([customer, technology])
        await db.flush()
        product = Product(
            part_number="QA-001",
            description="Producto de ensayo",
            plant_id=plant.id,
            customer_id=customer.id,
            status="Released",
            version=1,
        )
        db.add(product)
        await db.flush()
        diagram = Flowchart(
            title="Proceso de ensayo",
            flowchart_code="QA-FC-001",
            plant_id=plant.id,
            product_id=product.id,
            owner_id=user.id,
            created_by=user.id,
            status="Approved",
            version=1,
        )
        db.add(diagram)
        await db.flush()
        step = FlowchartStep(
            flowchart_id=diagram.id,
            technology_id=technology.id,
            step_number=10,
            sub_step=0,
            symbol_type="operation",
            responsible_department="Calidad",
            product_characteristics="Dimensión",
            process_characteristics="Inspección",
            target="10 ± 1 mm",
        )
        db.add(step)
        await db.flush()
        for count in [100, 500, 1000]:
            doc = PfmeaHeader(
                flowchart_id=diagram.id,
                plant_id=plant.id,
                owner_id=user.id,
                project_name=f"Ensayo {count} filas",
                customer=customer.company_name,
                part_number=product.part_number,
                version=1,
                pfmea_id_number=f"QA-PFMEA-{count}",
                moc_status="Draft",
                status="Draft",
            )
            db.add(doc)
            await db.flush()
            db.add(
                PfmeaTeamMember(
                    pfmea_id=doc.id,
                    user_id=user.id,
                    role_in_team="PFMEA Owner",
                    department="Calidad",
                )
            )
            for n in range(count):
                db.add(
                    PfmeaWorksheetRow(
                        pfmea_id=doc.id,
                        flowchart_step_id=step.id,
                        station_operation="10 – Inspección",
                        failure_mode=f"Dimensión fuera de rango {n + 1}",
                        severity=5,
                        occurrence=3,
                        detection=2,
                        action_priority="L",
                        sequence_order=(n + 1) * 10,
                        prevention_controls="Calibración",
                        detection_controls="Medición",
                    )
                )
        approved = PfmeaHeader(
            flowchart_id=diagram.id,
            plant_id=plant.id,
            owner_id=user.id,
            project_name="PFMEA aprobado sintético",
            customer=customer.company_name,
            part_number=product.part_number,
            version=1,
            pfmea_id_number="QA-PFMEA-CP",
            moc_status="Approved",
            status="Approved",
        )
        db.add(approved)
        await db.flush()
        db.add(
            PfmeaTeamMember(
                pfmea_id=approved.id,
                user_id=user.id,
                role_in_team="PFMEA Owner",
                department="Calidad",
            )
        )
        row = PfmeaWorksheetRow(
            pfmea_id=approved.id,
            flowchart_step_id=step.id,
            station_operation="Inspección",
            failure_mode="Dimensión crítica",
            severity=9,
            occurrence=1,
            detection=7,
            action_priority="H",
            sequence_order=10,
        )
        db.add(row)
        await db.flush()
        cp = ControlPlan(
            pfmea_project_id=approved.id,
            flowchart_id=diagram.id,
            control_plan_code="QA-CP-001",
            title="Plan de ensayo",
            start_date=date.today(),
            owner_id=user.id,
            created_by=user.id,
            status="Draft",
            version=1,
        )
        db.add(cp)
        await db.flush()
        db.add(
            ControlPlanItem(
                control_plan_id=cp.id,
                item_sequence=10,
                item_name="Dimensión crítica",
                pfmea_worksheet_row_id=row.id,
                source_row_id=row.id,
                characteristic="Dimensión",
                classification="CC",
                specification="10 ± 1",
                measurement_method="Calibrador",
                sample_size=5,
                sample_frequency="Cada hora",
                responsible_person_id=user.id,
                reaction_plan="Detener proceso y segregar material",
            )
        )
        await db.commit()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=8014, log_level="warning")
    )
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run())
