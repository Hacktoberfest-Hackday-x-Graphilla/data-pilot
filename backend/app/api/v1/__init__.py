from fastapi import APIRouter
from .upload import router as upload_router
from .analysis import router as analysis_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(upload_router, tags=["Datasets"])
api_v1_router.include_router(analysis_router, tags=["Analysis & Tools"])

__all__ = ["api_v1_router"]
