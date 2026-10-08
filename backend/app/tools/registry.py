from typing import Any, Callable
import pandas as pd

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
        "description": "Generates high-level profile of the entire dataset, including row/col counts, column types, missing value percentages, and sample rows.",
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
        "description": "Groups dataset by a categorical column and calculates aggregate comparisons (mean, sum, count, median, min, max) on numerical columns.",
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

def execute_tool(df: pd.DataFrame, tool_name: str, parameters: dict[str, Any]) -> Any:
    """Executes a registered tool against the provided dataframe with given parameters."""
    if tool_name not in TOOL_MAP:
        raise ValueError(f"Unknown tool '{tool_name}'. Available tools: {list(TOOL_MAP.keys())}")

    func = TOOL_MAP[tool_name]
    if tool_name == "profile_dataset":
        return func(df)
    return func(df, **parameters)
