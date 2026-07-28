import asyncio
import traceback
from app.core.db import AsyncSessionLocal
from app.services.flowchart_service import list_flowcharts
from app.schemas.flowchart import FlowchartRead

async def main():
    async with AsyncSessionLocal() as session:
        try:
            print("Listing flowcharts from service...")
            flowcharts = await list_flowcharts(session)
            print(f"Found {len(flowcharts)} flowcharts.")
            for i, fc in enumerate(flowcharts):
                print(f"\nFlowchart {i}: ID={fc.id}, Title={fc.title}, Product ID={fc.product_id}")
                if fc.product:
                    print(f"  Product: ID={fc.product.id}, Name={fc.product.customer_name}, Part={fc.product.part_number}")
                else:
                    print("  Product: None")
                try:
                    # Let's try validation
                    read_model = FlowchartRead.model_validate(fc)
                    print(f"  Validation OK: {read_model}")
                except Exception as ve:
                    print("  Validation FAILED:")
                    traceback.print_exc()
        except Exception as e:
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
