import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.region import Region
from app.models.plant import Plant
from app.models.role import Role
from app.models.user import User
from app.core.hashing import hash_password

logger = logging.getLogger(__name__)

async def seed_db(db: AsyncSession) -> None:
    """
    Defensive DB seed for roles, regions, plants, and the principal Administrator.
    """
    try:
        # 1. Seed default Region (NAFTA) if not present
        stmt = select(Region).limit(1)
        result = await db.execute(stmt)
        region = result.scalars().first()
        if not region:
            region = Region(
                name="NAFTA",
                code="NA",
                description="North American Free Trade Agreement Region",
                is_active=True
            )
            db.add(region)
            await db.flush()
            logger.info("Default region (NAFTA) seeded.")
        
        # 2. Seed default Plant (Puebla Plant) if not present
        stmt = select(Plant).limit(1)
        result = await db.execute(stmt)
        plant = result.scalars().first()
        if not plant:
            plant = Plant(
                region_id=region.id,
                name="Puebla Plant",
                code="APG_PUE",
                address="APG Puebla Industrial Park, Puebla, México",
                is_active=True
            )
            db.add(plant)
            await db.flush()
            logger.info("Default plant (Puebla Plant) seeded.")

        # 3. Seed Roles if empty
        roles_to_seed = [
            ("Administrator", "System Administrator with full access"),
            ("PFMEA Owner", "FMEA Process Owner responsible for document lifecycle"),
            ("Team Member", "Cross-Functional Team Member participating in FMEAs"),
            ("Viewer", "Read-only access to FMEAs and Control Plans"),
            ("Process Engineer", "Process Engineer focused on flowchart and instruction sheets")
        ]
        
        roles_map = {}
        for role_name, desc in roles_to_seed:
            stmt = select(Role).where(func.lower(Role.name) == role_name.lower())
            res = await db.execute(stmt)
            role = res.scalars().first()
            if not role:
                role = Role(
                    name=role_name,
                    description=desc,
                    is_active=True
                )
                db.add(role)
                await db.flush()
                logger.info(f"Role '{role_name}' seeded.")
            roles_map[role_name.lower()] = role

        # 4. Seed main Administrator account if not present
        admin_email = "antonio.tlaque@adlerpelzer.com"
        stmt = select(User).where(func.lower(User.email) == admin_email.lower())
        result = await db.execute(stmt)
        admin_user = result.scalars().first()
        
        if not admin_user:
            # Generate a secure temporary password
            temp_password = "APGPuebla2026!"
            hashed_pwd = hash_password(temp_password)
            
            # Find Admin role id
            admin_role = roles_map.get("administrator")
            if not admin_role:
                # Fallback role lookup
                stmt = select(Role).where(func.lower(Role.name).in_(["administrator", "admin"]))
                res = await db.execute(stmt)
                admin_role = res.scalars().first()
            
            admin_user = User(
                role_id=admin_role.id if admin_role else None,
                plant_id=plant.id,
                full_name="Antonio Tlaque",
                email=admin_email,
                password_hash=hashed_pwd,
                employment_position="System Administrator",
                is_active=True
            )
            db.add(admin_user)
            await db.flush()
            
            print("\n" + "*"*80)
            print(f"🔒 [ADMINISTRATOR ACCOUNT SEEDED]")
            print(f"EMAIL: {admin_email}")
            print(f"TEMPORARY PASSWORD: {temp_password}")
            print("Please change this password immediately after your first successful login!")
            print("*"*80 + "\n")
            logger.info(f"Principal administrator '{admin_email}' successfully seeded.")
            
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error during DB seeding: {e}")
        raise e

async def seed_admin_user() -> None:
    """Helper entry point for lifespan event that creates its own session."""
    async with AsyncSessionLocal() as session:
        await seed_db(session)
