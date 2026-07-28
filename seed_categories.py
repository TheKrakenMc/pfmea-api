import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.technology_category import TechnologyCategory

PREDEFINED_CATEGORIES = [
    'Inyección',
    'Ensamble',
    'Torque',
    'Soldadura',
    'Estampado',
    'Pintura',
    'Corte',
    'Tratamiento Térmico',
]

async def seed_categories():
    async with SessionLocal() as session:
        for name in PREDEFINED_CATEGORIES:
            # Check if exists
            result = await session.execute(select(TechnologyCategory).where(TechnologyCategory.name == name))
            if not result.scalars().first():
                cat = TechnologyCategory(name=name)
                session.add(cat)
        
        await session.commit()
        print("Categories seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_categories())
