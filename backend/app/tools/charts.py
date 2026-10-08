from typing import Any, Optional
import pandas as pd
from app.tools.profiling import _sanitize_val

SUPPORTED_CHART_TYPES = {"bar", "line", "scatter", "histogram", "box"}

def create_chart(
    df: pd.DataFrame,
    chart_type: str,
    x: Optional[str] = None,
    y: Optional[str] = None,
    group_by: Optional[str] = None,
    title: Optional[str] = None,
    aggregation: Optional[str] = "mean",
    max_data_points: int = 100,
    **kwargs: Any
) -> dict[str, Any]:
    """Generates declarative chart specifications and data points for frontend visualization."""
    chart_type = chart_type.lower()
    if chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(f"Chart type '{chart_type}' is not supported. Supported: {list(SUPPORTED_CHART_TYPES)}")

    x_col = x or kwargs.get("x_axis")
    if not x_col:
        raise ValueError("Missing required 'x' column for chart creation.")
    x = x_col

    y_col = y or kwargs.get("y_axis")
    y = y_col

    agg = aggregation or kwargs.get("aggregations") or "mean"
    if isinstance(agg, list):
        agg = agg[0] if agg else "mean"

    if x not in df.columns:
        raise ValueError(f"Column '{x}' does not exist in dataset.")

    if y and y not in df.columns:
        raise ValueError(f"Column '{y}' does not exist in dataset.")

    default_title = f"{chart_type.capitalize()} of {y or x}" + (f" vs {x}" if y else "")
    chart_title = title or default_title

    chart_spec: dict[str, Any] = {
        "chart_type": chart_type,
        "title": chart_title,
        "x_axis": x,
        "y_axis": y,
        "group_by": group_by,
        "data": [],
    }

    if chart_type in ("bar", "line"):
        if y:
            # Aggregate if y is provided
            agg_func = aggregation if aggregation in ("mean", "sum", "count", "median") else "mean"
            grouped = df.groupby(x, observed=True)[y].agg(agg_func).reset_index()
            # Limit points to avoid massive payloads
            if len(grouped) > max_data_points:
                grouped = grouped.sort_values(by=y, ascending=False).head(max_data_points)
            
            for _, r in grouped.iterrows():
                chart_spec["data"].append({
                    "x": _sanitize_val(r[x]),
                    "y": _sanitize_val(r[y]),
                })
        else:
            # Frequency count of x
            counts = df[x].value_counts().head(max_data_points).reset_index()
            counts.columns = [x, "count"]
            for _, r in counts.iterrows():
                chart_spec["data"].append({
                    "x": _sanitize_val(r[x]),
                    "y": int(r["count"]),
                })

    elif chart_type == "scatter":
        if not y:
            raise ValueError("Scatter chart requires both 'x' and 'y' columns.")
        clean_df = df[[x, y]].dropna()
        if len(clean_df) > max_data_points:
            clean_df = clean_df.sample(n=max_data_points, random_state=42)

        for _, r in clean_df.iterrows():
            chart_spec["data"].append({
                "x": _sanitize_val(r[x]),
                "y": _sanitize_val(r[y]),
            })

    elif chart_type == "histogram":
        series = df[x].dropna()
        if pd.api.types.is_numeric_dtype(series):
            # Bin numerical data
            bins = 15
            counts, bin_edges = pd.cut(series, bins=bins, retbins=True, labels=False)
            bin_counts = counts.value_counts().sort_index()
            for b_idx, count in bin_counts.items():
                bin_label = f"{round(float(bin_edges[b_idx]), 2)} - {round(float(bin_edges[b_idx+1]), 2)}"
                chart_spec["data"].append({
                    "bin": bin_label,
                    "count": int(count),
                })
        else:
            counts = series.value_counts().head(max_data_points)
            for val, count in counts.items():
                chart_spec["data"].append({
                    "bin": _sanitize_val(val),
                    "count": int(count),
                })

    elif chart_type == "box":
        # Five-number summary for box plot
        series = df[x].dropna() if not y else df[y].dropna()
        if not pd.api.types.is_numeric_dtype(series):
            raise ValueError("Box plot requires a numerical column.")
        
        q25 = float(series.quantile(0.25))
        q50 = float(series.median())
        q75 = float(series.quantile(0.75))
        iqr = q75 - q25
        min_val = max(float(series.min()), q25 - 1.5 * iqr)
        max_val = min(float(series.max()), q75 + 1.5 * iqr)

        chart_spec["data"] = [{
            "column": y or x,
            "min": _sanitize_val(min_val),
            "q25": _sanitize_val(q25),
            "median": _sanitize_val(q50),
            "q75": _sanitize_val(q75),
            "max": _sanitize_val(max_val),
        }]

    return chart_spec
