import time
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    ProfileReport,
    ToolExecutionRequest,
    ToolExecutionResponse,
)
from app.services.dataset_store import dataset_store
from app.tools.registry import (
    GEMINI_FUNCTION_DECLARATIONS,
    TOOL_MAP,
    execute_tool,
)
from app.tools.profiling import profile_dataset

router = APIRouter()

@router.post("/datasets/{dataset_id}/profile", response_model=ProfileReport)
def profile_dataset_endpoint(dataset_id: str):
    """Executes full profile analysis on the specified dataset."""
    df = dataset_store.get_dataset(dataset_id)
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )

    metadata = dataset_store.get_metadata(dataset_id)
    filename = metadata["filename"] if metadata else "dataset.csv"

    profile_data = profile_dataset(df)
    
    return ProfileReport(
        dataset_id=dataset_id,
        filename=filename,
        **profile_data,
    )

@router.post("/datasets/{dataset_id}/tools/execute", response_model=ToolExecutionResponse)
def execute_tool_endpoint(dataset_id: str, request: ToolExecutionRequest):
    """Executes a specific analytical tool on a dataset by name with arguments."""
    df = dataset_store.get_dataset(dataset_id)
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' not found.",
        )

    if request.tool_name not in TOOL_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{request.tool_name}' is not recognized. Available tools: {list(TOOL_MAP.keys())}",
        )

    start_time = time.perf_counter()
    try:
        result = execute_tool(df, request.tool_name, request.parameters)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ToolExecutionResponse(
            dataset_id=dataset_id,
            tool_name=request.tool_name,
            success=True,
            data=result,
            error=None,
            execution_time_ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ToolExecutionResponse(
            dataset_id=dataset_id,
            tool_name=request.tool_name,
            success=False,
            data=None,
            error=str(e),
            execution_time_ms=elapsed_ms,
        )

@router.get("/tools")
def get_available_tools():
    """Lists all available analytical tools and their Gemini function calling definitions."""
    return {
        "tools": list(TOOL_MAP.keys()),
        "gemini_function_declarations": GEMINI_FUNCTION_DECLARATIONS,
    }
