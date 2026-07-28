import asyncio
from app.core.db import AsyncSessionLocal
from app.models.technology import Technology
from sqlalchemy import select

PLANT_OPERATIONS = [
  # Assembly
  { 'code': 'ASM-01', 'name': 'Assembly',           'category': 'assembly' },
  { 'code': 'ASM-02', 'name': 'Sub-Assembly',       'category': 'assembly' },
  { 'code': 'ASM-03', 'name': 'Riveting',           'category': 'assembly' },
  { 'code': 'ASM-04', 'name': 'Welding (MIG)',      'category': 'assembly' },
  { 'code': 'ASM-05', 'name': 'Welding (Spot)',     'category': 'assembly' },
  { 'code': 'ASM-06', 'name': 'Adhesive Bonding',   'category': 'assembly' },

  # Forming
  { 'code': 'FRM-01', 'name': 'Stamping',           'category': 'forming' },
  { 'code': 'FRM-02', 'name': 'Deep Drawing',       'category': 'forming' },
  { 'code': 'FRM-03', 'name': 'Bending',            'category': 'forming' },
  { 'code': 'FRM-04', 'name': 'Roll Forming',       'category': 'forming' },
  { 'code': 'FRM-05', 'name': 'PU Foaming',         'category': 'forming' },
  { 'code': 'FRM-06', 'name': 'Injection Molding',  'category': 'forming' },
  { 'code': 'FRM-07', 'name': 'AirLay',             'category': 'forming' },

  # Inspection & Testing
  { 'code': 'INS-01', 'name': 'Visual Inspection',    'category': 'inspection' },
  { 'code': 'INS-02', 'name': 'CMM Measurement',      'category': 'inspection' },
  { 'code': 'INS-03', 'name': 'Functional Test',      'category': 'inspection' },
  { 'code': 'INS-04', 'name': 'Leak Test',            'category': 'inspection' },
  { 'code': 'INS-05', 'name': 'Torque Verification',  'category': 'inspection' },

  # Finishing
  { 'code': 'FIN-01', 'name': 'E-Coat',              'category': 'finishing' },
  { 'code': 'FIN-02', 'name': 'Painting',            'category': 'finishing' },
  { 'code': 'FIN-03', 'name': 'Deburring',           'category': 'finishing' },
  { 'code': 'FIN-04', 'name': 'Polishing',           'category': 'finishing' },
  { 'code': 'FIN-05', 'name': 'Heat Treatment',      'category': 'finishing' },

  # Material Handling
  { 'code': 'MAT-01', 'name': 'Receiving',           'category': 'material' },
  { 'code': 'MAT-02', 'name': 'Storage (WIP)',       'category': 'material' },
  { 'code': 'MAT-03', 'name': 'Packaging',           'category': 'material' },
  { 'code': 'MAT-04', 'name': 'Shipping',            'category': 'material' },

  # Chemical Processes
  { 'code': 'CHM-01', 'name': 'Cleaning / Washing',  'category': 'chemical' },
  { 'code': 'CHM-02', 'name': 'Phosphating',         'category': 'chemical' },
  { 'code': 'CHM-03', 'name': 'Anodizing',           'category': 'chemical' },
]

async def seed_technologies():
    async with AsyncSessionLocal() as session:
        for op in PLANT_OPERATIONS:
            # Check if it exists
            stmt = select(Technology).where(Technology.code == op['code'])
            result = await session.execute(stmt)
            existing = result.scalars().first()
            if not existing:
                print(f"Adding technology: {op['code']} - {op['name']}")
                tech = Technology(
                    code=op['code'],
                    name=op['name'],
                    category=op['category']
                )
                session.add(tech)
            else:
                print(f"Technology {op['code']} already exists, skipping.")
        
        await session.commit()
        print("Seed completed.")

if __name__ == "__main__":
    asyncio.run(seed_technologies())
