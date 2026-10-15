"""Run explicitly: python -m scripts.provision_admin. Never prints credentials."""

import argparse
import asyncio
from getpass import getpass
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models import User, Role, Plant
from app.models.auth_session import UserPlant
from app.core.hashing import hash_password
from app.services.seed import seed_db


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset-existing",action="store_true",help="Explicitly replace an active Administrator credential during maintenance")
    args=parser.parse_args()
    email = input("Administrator email: ").strip().lower()
    password = getpass("Temporary password (8–72 UTF-8 bytes): ")
    if not email or "@" not in email or not 8 <= len(password.encode()) <= 72:
        raise ValueError("Invalid email or password length")
    async with AsyncSessionLocal() as db:
        await seed_db(db)
        existing=(await db.scalars(select(User).where(User.email == email))).first()
        if existing and not args.reset_existing:
            raise ValueError("Account already exists; use recovery or explicitly request --reset-existing")
        role = (
            await db.scalars(select(Role).where(Role.name == "Administrator"))
        ).one()
        if existing:
            if existing.role_id!=role.id or not existing.is_active or existing.deleted_at is not None:
                raise ValueError("Only an active Administrator can be reset by this command")
            from app.services.session_service import revoke_user_sessions
            existing.password_hash=hash_password(password)
            existing.is_verified=True
            existing.must_change_password=True
            await revoke_user_sessions(db,existing.id)
            await db.commit()
            print("Administrator credential replaced; sessions revoked; password change required")
            return
        plant = (
            await db.scalars(select(Plant).where(Plant.is_active.is_(True)))
        ).first()
        user = User(
            email=email,
            password_hash=hash_password(password),
            role_id=role.id,
            plant_id=plant.id if plant else None,
            is_verified=True,
            must_change_password=True,
        )
        db.add(user)
        await db.flush()
        if plant:
            db.add(UserPlant(user_id=user.id, plant_id=plant.id))
        await db.commit()
    print("Administrator created; password change is required at first login.")


if __name__ == "__main__":
    asyncio.run(main())
