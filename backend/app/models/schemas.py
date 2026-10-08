from typing import Any, Optional
from pydantic import BaseModel, Field

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    category: str = Field(description="Column category: numeric, categorical, datetime, boolean, other")
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: list[Any] = Field(default_factory=list)

class ProfileReport(BaseModel):
    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    memory_mb: float
    duplicate_rows: int
    columns: list[ColumnProfile]
    numeric_columns: list[str]
    categorical_columns: list[str]
    sample_rows: list[dict[str, Any]]

class DatasetSummary(BaseModel):
    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    columns: list[str]
    memory_mb: float
    created_at: str

class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)

class ToolExecutionResponse(BaseModel):
    dataset_id: str
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float
