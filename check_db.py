import asyncio
from app.core.db import AsyncSessionLocal
from sqlalchemy import text

async def run():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'pfmea' AND table_name = 'products';"))
        for row in res:
            print(row)

if __name__ == '__main__':
    asyncio.run(run())
