import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import selectinload

from app.models.flowchart import Flowchart
from app.models.plant import Plant

async def run_update():
    # Setup engine
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/pfmea')
    async with AsyncSession(engine) as db:
        # Fetch all flowcharts with their plants
        result = await db.execute(select(Flowchart).options(selectinload(Flowchart.product)))
        flowcharts = result.scalars().all()
        
        # Group flowcharts by plant_id
        plant_ids = {fc.plant_id for fc in flowcharts if fc.plant_id}
        
        # Get plant codes
        plant_codes = {}
        for pid in plant_ids:
            res = await db.execute(select(Plant.code).where(Plant.id == pid))
            code = res.scalar_one_or_none()
            if code:
                plant_codes[pid] = code.upper().replace(" ", "_")
        
        # Process each flowchart
        updates_count = 0
        
        # We need to maintain a sequence per plant
        # We'll just order flowcharts by id to preserve order
        flowcharts.sort(key=lambda x: x.id)
        
        # Keep track of current sequence per plant
        seq_per_plant = {}
        
        for fc in flowcharts:
            if not fc.flowchart_code or fc.flowchart_code.startswith("FC-"):
                pid = fc.plant_id
                plant_code = plant_codes.get(pid, "PLANT")
                
                # Get sequence
                if pid not in seq_per_plant:
                    seq_per_plant[pid] = 1
                
                seq = seq_per_plant[pid]
                seq_per_plant[pid] += 1
                
                # Use current year for retroactively generated ones, or creation year if preferred.
                year = fc.created_at.year if fc.created_at else datetime.now(timezone.utc).year
                version = fc.version or 1
                
                new_code = f"{plant_code}_FLOWCHART_{seq:03d}_{year}_{version}"
                
                print(f"Updating flowchart ID {fc.id} from {fc.flowchart_code} to {new_code}")
                fc.flowchart_code = new_code
                db.add(fc)
                updates_count += 1
                
        if updates_count > 0:
            await db.commit()
            print(f"Successfully updated {updates_count} flowcharts.")
        else:
            print("No flowcharts needed updating.")

if __name__ == "__main__":
    asyncio.run(run_update())
