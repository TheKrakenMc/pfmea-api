import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.db import AsyncSessionLocal
from app.services.product_service import get_product
import app.models

async def main():
    async with AsyncSessionLocal() as db:
        try:
            product = await get_product(db, 5)
            print("Product found:", product.part_number)
            print("Technologies:", product.technologies)
            print("Parameters:", product.parameters)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
