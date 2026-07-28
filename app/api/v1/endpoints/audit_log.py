from fastapi import APIRouter

router = APIRouter(prefix="/audit-log", tags=["Audit Log"])

@router.get("/")
async def get_dummy():
    return {"message": "Hello from Audit Log"}
