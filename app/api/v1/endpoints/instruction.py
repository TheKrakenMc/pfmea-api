from fastapi import APIRouter

router = APIRouter(prefix="/instruction", tags=["Instruction"])

@router.get("/")
async def get_dummy():
    return {"message": "Hello from Instruction"}
