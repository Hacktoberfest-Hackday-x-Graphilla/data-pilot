from fastapi import APIRouter, status
from .upload import router as upload_router, upload_dataset
from .analysis import router as analysis_router
from app.models.schemas import DatasetSummary

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(upload_router, tags=["Datasets"])
api_v1_router.add_api_route(
    "/upload",
    upload_dataset,
    methods=["POST"],
    response_model=DatasetSummary,
    status_code=status.HTTP_201_CREATED,
    tags=["Datasets"],
    summary="Upload Dataset (Alias)",
)
api_v1_router.include_router(analysis_router, tags=["Analysis & Tools"])

__all__ = ["api_v1_router"]

