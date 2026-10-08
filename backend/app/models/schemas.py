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

# Milestone 2: AI Agent Schemas

class ToolTraceItem(BaseModel):
    tool_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    success: bool
    summary: Optional[str] = None
    data: Optional[Any] = None

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question about the dataset")

class ChatResponse(BaseModel):
    dataset_id: str
    question: str
    answer: str
    tool_trace: list[ToolTraceItem] = Field(default_factory=list)
    suggested_charts: list[dict[str, Any]] = Field(default_factory=list)

class InvestigationFinding(BaseModel):
    category: str = Field(description="Category of finding: distribution, correlation, anomaly, comparison, trend")
    title: str
    description: str
    importance: str = Field(default="medium", description="Importance level: high, medium, low")
    evidence: dict[str, Any] = Field(default_factory=dict)

class InvestigateResponse(BaseModel):
    dataset_id: str
    summary: str
    findings: list[InvestigationFinding] = Field(default_factory=list)
    tool_trace: list[ToolTraceItem] = Field(default_factory=list)
    charts: list[dict[str, Any]] = Field(default_factory=list)

# Milestone 3: Questionless Dataset Discovery Schemas

class DiscoveryFinding(BaseModel):
    id: str = Field(description="Unique candidate identifier, e.g. corr_001")
    type: str = Field(description="Discovery category: correlation, group_difference, category_numeric, time_pattern, interaction, data_quality")
    title: str = Field(description="Human-readable discovery title")
    columns: list[str] = Field(default_factory=list, description="Relevant dataset columns")
    metric: dict[str, Any] = Field(default_factory=dict, description="Key calculated statistical metric")
    evidence: dict[str, Any] = Field(default_factory=dict, description="Detailed numerical evidence computed by Python")
    explanation: str = Field(description="Analytical explanation of the discovery")
    caution: Optional[str] = Field(default=None, description="Cautionary context regarding causation or sample limitations")
    importance: str = Field(default="medium", description="Importance rating: high, medium, low")
    discovery_score: float = Field(default=0.0, description="Deterministic statistical score before LLM ranking")

class DiscoverySummary(BaseModel):
    rows: int
    columns: int
    candidates_examined: int
    findings_returned: int
    execution_time_ms: float = 0.0

class DiscoveryRequest(BaseModel):
    dataset_id: str
    max_findings: int = Field(default=5, ge=1, le=20)

class DiscoveryResponse(BaseModel):
    dataset_id: str
    filename: str
    summary: DiscoverySummary
    findings: list[DiscoveryFinding]

