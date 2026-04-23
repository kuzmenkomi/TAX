from __future__ import annotations

from fastapi import APIRouter

from app.routers.root import router as root_router
from app.routers.v1 import router as v1_router

api_router = APIRouter()
api_router.include_router(root_router)
api_router.include_router(v1_router, prefix="/v1")

__all__ = ["api_router"]
