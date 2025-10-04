from fastapi import APIRouter

from .status import router as status_router
from .analyze import router as analyze_router


api_v1_router = APIRouter()
api_v1_router.include_router(status_router)
api_v1_router.include_router(analyze_router)


