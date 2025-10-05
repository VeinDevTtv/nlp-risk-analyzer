from fastapi import APIRouter

from .status import router as status_router
from .analyze import router as analyze_router
from .auth import router as auth_router
from .watchlist import router as watchlist_router


api_v1_router = APIRouter()
api_v1_router.include_router(status_router)
api_v1_router.include_router(analyze_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(watchlist_router)


