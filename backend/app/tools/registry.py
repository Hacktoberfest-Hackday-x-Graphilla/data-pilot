from typing import Any, Callable, Optional
import pandas as pd
from google.genai import types

from app.tools.profiling import profile_dataset
from app.tools.statistics import calculate_statistics
from app.tools.comparisons import group_and_compare
from app.tools.anomalies import detect_anomalies
from app.tools.charts import create_chart
from app.tools.correlations import find_correlations

TOOL_MAP: dict[str, Callable] = {
    "profile_dataset": profile_dataset,
    "calculate_statistics": calculate_statistics,
    "group_and_compare": group_and_compare,
    "detect_anomalies": detect_anomalies,
    "create_chart": create_chart,
    "find_correlations": find_correlations,
}

# Declarations ready for Gemini function calling (Tool declarations)
GEMINI_FUNCTION_DECLARATIONS = [
    {
        "name": "profile_dataset",
        "description": "Generates a high-level profile of the entire dataset, including row/col counts, column data types, missing value percentages, and sample records.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "calculate_statistics",
        "description": "Calculates descriptive statistics (mean, median, std, quartiles, IQR, skewness, mode, frequency counts) for specific or all columns.",
        "parameters": {
            "type": "object",
            "properties": {
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of column names to analyze. If omitted, analyzes all columns.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "group_and_compare",
        "description": "Groups dataset by a categorical column and calculates aggregate comparisons (mean, sum, count, median, min, max, std) on numerical columns.",
        "parameters": {
            "type": "object",
            "properties": {
                "group_by": {
                    "type": "string",
                    "description": "The categorical column name to group by.",
                },
                "metric_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of numeric column names to aggregate.",
                },
                "aggregations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Aggregation operations to perform: mean, sum, count, median, min, max, std. Defaults to ['mean', 'count'].",
                },
            },
            "required": ["group_by", "metric_columns"],
        },
    },
    {
        "name": "detect_anomalies",
        "description": "Detects outliers and anomalies in numerical columns using IQR (Interquartile Range) or Z-score methods.",
        "parameters": {
            "type": "object",
            "properties": {
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of numerical columns to scan for anomalies. If omitted, scans all numerical columns.",
                },
                "method": {
                    "type": "string",
                    "enum": ["iqr", "zscore"],
                    "description": "Anomaly detection method. Defaults to 'iqr'.",
                },
                "threshold": {
                    "type": "number",
                    "description": "Sensitivity multiplier. Default is 1.5 for IQR, 3.0 for Z-score.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_chart",
        "description": "Generates chart configuration data points for visualization (bar, line, scatter, histogram, box).",
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "scatter", "histogram", "box"],
                    "description": "Type of visualization.",
                },
                "x": {
                    "type": "string",
                    "description": "Column for x-axis.",
                },
                "y": {
                    "type": "string",
                    "description": "Column for y-axis (required for scatter, optional for bar/line).",
                },
                "title": {
                    "type": "string",
                    "description": "Optional title for the chart.",
                },
                "aggregation": {
                    "type": "string",
                    "enum": ["mean", "sum", "count", "median"],
                    "description": "Aggregation method when y is plotted over categorical x. Default is 'mean'.",
                },
            },
            "required": ["chart_type", "x"],
        },
    },
    {
        "name": "find_correlations",
        "description": "Computes correlation matrix and identifies top correlated pairs among numerical features.",
        "parameters": {
            "type": "object",
            "properties": {
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of numerical columns to include. If omitted, includes all numerical columns.",
                },
                "method": {
                    "type": "string",
                    "enum": ["pearson", "spearman", "kendall"],
                    "description": "Correlation method. Default is 'pearson'.",
                },
                "min_threshold": {
                    "type": "number",
                    "description": "Minimum absolute correlation to report. Default is 0.0.",
                },
            },
            "required": [],
        },
    },
]

def get_genai_tools() -> list[types.Tool]:
    """Wraps registered tool declarations into Google GenAI SDK Tool specifications."""
    return [types.Tool(function_declarations=GEMINI_FUNCTION_DECLARATIONS)]

def execute_tool(df: pd.DataFrame, tool_name: str, parameters: Optional[dict[str, Any]] = None) -> Any:
    """Executes a registered tool against the provided dataframe with given parameters."""
    if tool_name not in TOOL_MAP:
        raise ValueError(f"Unknown tool '{tool_name}'. Available tools: {list(TOOL_MAP.keys())}")

    func = TOOL_MAP[tool_name]
    params = parameters or {}
    if tool_name == "profile_dataset":
        return func(df)
    return func(df, **params)

def summarize_tool_result(tool_name: str, result: Any) -> str:
    """Provides a concise, safe summary description of tool execution."""
    if not isinstance(result, dict):
        return f"Executed {tool_name}"
        
    if tool_name == "profile_dataset":
        return f"Profiled dataset: {result.get('row_count', 0)} rows, {result.get('column_count', 0)} columns"
    elif tool_name == "calculate_statistics":
        num_cnt = len(result.get("numeric_stats", {}))
        cat_cnt = len(result.get("categorical_stats", {}))
        return f"Calculated stats for {num_cnt} numeric and {cat_cnt} categorical columns"
    elif tool_name == "group_and_compare":
        return f"Grouped by '{result.get('group_by')}' across {result.get('total_groups', 0)} groups"
    elif tool_name == "detect_anomalies":
        cols = list(result.get("anomalies", {}).keys())
        return f"Anomaly scan across {len(cols)} columns ({', '.join(cols[:3])})"
    elif tool_name == "create_chart":
        return f"Created {result.get('chart_type')} chart: '{result.get('title')}' with {len(result.get('data', []))} data points"
    elif tool_name == "find_correlations":
        pairs = len(result.get("top_correlated_pairs", []))
        return f"Found {pairs} notable correlated feature pairs"
    return f"Executed {tool_name}"
