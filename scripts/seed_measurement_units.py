import asyncio
import os
import re
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.core.db import AsyncSessionLocal
import app.models # Ensure all models are registered
from app.models.measurement_unit import MeasurementUnit

async def seed_units():
    md_file = r"C:\Users\program jr\Documents\GitHub\pfmea\pfmea-ui\measurement_units_202607230958.md"
    
    if not os.path.exists(md_file):
        print(f"File not found: {md_file}")
        return
        
    with open(md_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    units = []
    for line in lines:
        if line.startswith("|") and not line.startswith("|id|") and not line.startswith("|--|"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                # parts[0] is empty because line starts with |
                # id = parts[1]
                desc = parts[2]
                sym = parts[3]
                mag = parts[4]
                units.append(MeasurementUnit(description=desc, symbology=sym, magnitude=mag))
                
    if not units:
        print("No units found to seed.")
        return
        
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select
        result = await db.execute(select(MeasurementUnit).limit(1))
        if result.scalar_one_or_none():
            print("Measurement units already seeded.")
            return
            
        db.add_all(units)
        await db.commit()
        print(f"Successfully seeded {len(units)} measurement units.")

if __name__ == "__main__":
    asyncio.run(seed_units())
