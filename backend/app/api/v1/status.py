from fastapi import APIRouter

router = APIRouter(prefix="/v1")


@router.get("/health")
async def v1_health():
    return {"status": "ok"}
