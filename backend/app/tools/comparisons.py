from typing import Any, Optional
import pandas as pd
from app.tools.profiling import _sanitize_val

SUPPORTED_AGGS = {"mean", "sum", "count", "median", "min", "max", "std"}

def group_and_compare(
    df: pd.DataFrame,
    group_by: str,
    metric_columns: list[str],
    aggregations: Optional[list[str]] = None
) -> dict[str, Any]:
    """Groups dataset by categorical feature and computes comparative aggregations across metric columns."""
    if group_by not in df.columns:
        raise ValueError(f"Group column '{group_by}' does not exist in dataset.")

    valid_metrics = [c for c in metric_columns if c in df.columns]
    if not valid_metrics:
        raise ValueError(f"None of the metric columns {metric_columns} exist in dataset.")

    aggs = [a.lower() for a in (aggregations or ["mean", "count"])]
    invalid_aggs = [a for a in aggs if a not in SUPPORTED_AGGS]
    if invalid_aggs:
        raise ValueError(f"Unsupported aggregations: {invalid_aggs}. Supported: {list(SUPPORTED_AGGS)}")

    # Perform group by
    grouped = df.groupby(group_by, observed=True)

    agg_dict = {col: aggs for col in valid_metrics}
    agg_df = grouped.agg(agg_dict)

    # Flatten MultiIndex columns if multiple aggregations
    flat_rows = []
    if isinstance(agg_df.columns, pd.MultiIndex):
        agg_df.columns = [f"{col}_{func}" for col, func in agg_df.columns]

    for group_name, row in agg_df.iterrows():
        row_dict = {"group": _sanitize_val(group_name)}
        for col_name, val in row.items():
            row_dict[str(col_name)] = _sanitize_val(val)
        flat_rows.append(row_dict)

    return {
        "group_by": group_by,
        "metrics_evaluated": valid_metrics,
        "aggregations": aggs,
        "total_groups": len(flat_rows),
        "results": flat_rows,
    }
