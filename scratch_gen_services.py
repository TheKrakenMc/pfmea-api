import os

services = [
    "pfmea_project_service",
    "control_plan_service",
    "instruction_service"
]

endpoints = [
    "pfmea_project",
    "control_plan",
    "instruction",
    "audit_log",
    "process_analysis"
]

service_template = '''from sqlalchemy.ext.asyncio import AsyncSession

async def create_dummy(db: AsyncSession):
    pass
'''

endpoint_template = '''from fastapi import APIRouter

router = APIRouter(prefix="/{name}", tags=["{tag}"])

@router.get("/")
async def get_dummy():
    return {{"message": "Hello from {tag}"}}
'''

def to_title(snake):
    return ' '.join(word.capitalize() for word in snake.split('_'))

for s in services:
    path = f"app/services/{s}.py"
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(service_template)

for e in endpoints:
    path = f"app/api/v1/endpoints/{e}.py"
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(endpoint_template.format(name=e.replace('_', '-'), tag=to_title(e)))

print("Created services and endpoints")
