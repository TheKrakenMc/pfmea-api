from fastapi import APIRouter

router = APIRouter(prefix="/control-plan", tags=["Control Plan"])

@router.get("/")
async def get_dummy():
    return {"message": "Hello from Control Plan"}
