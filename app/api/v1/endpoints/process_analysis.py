from fastapi import APIRouter

router = APIRouter(prefix="/process-analysis", tags=["Process Analysis"])

@router.get("/")
async def get_dummy():
    return {"message": "Hello from Process Analysis"}
