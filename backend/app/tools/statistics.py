from typing import Any, Optional
import numpy as np
import pandas as pd
from app.tools.profiling import _sanitize_val

def calculate_statistics(
    df: pd.DataFrame,
    columns: Optional[Any] = None,
    **kwargs: Any
) -> dict[str, Any]:
    """Calculates summary statistics for numerical and categorical columns."""
    cols = columns if columns is not None else kwargs.get("column")
    if isinstance(cols, str):
        target_cols = [cols]
    elif cols:
        target_cols = [str(c) for c in cols]
    else:
        target_cols = [str(c) for c in df.columns]
    valid_cols = [c for c in target_cols if c in df.columns]

    if not valid_cols:
        raise ValueError(f"None of the requested columns {columns} exist in dataset.")

    results: dict[str, Any] = {"numeric_stats": {}, "categorical_stats": {}}

    for col in valid_cols:
        series = df[col]
        non_null = series.dropna()

        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            if len(non_null) == 0:
                results["numeric_stats"][col] = {
                    "count": 0,
                    "null_count": int(series.isna().sum()),
                    "message": "All values are null.",
                }
                continue

            q25 = float(non_null.quantile(0.25))
            q75 = float(non_null.quantile(0.75))
            iqr = q75 - q25

            skew = float(non_null.skew()) if len(non_null) > 2 else 0.0

            results["numeric_stats"][col] = {
                "count": int(len(non_null)),
                "null_count": int(series.isna().sum()),
                "mean": _sanitize_val(non_null.mean()),
                "std": _sanitize_val(non_null.std(ddof=1)) if len(non_null) > 1 else 0.0,
                "median": _sanitize_val(non_null.median()),
                "min": _sanitize_val(non_null.min()),
                "max": _sanitize_val(non_null.max()),
                "q25": _sanitize_val(q25),
                "q75": _sanitize_val(q75),
                "iqr": _sanitize_val(iqr),
                "skewness": _sanitize_val(skew),
                "sum": _sanitize_val(non_null.sum()),
            }
        else:
            # Categorical or Boolean statistics
            counts = series.value_counts(dropna=True)
            top_5 = []
            for val, count in counts.head(5).items():
                pct = round(count / len(series) * 100, 2) if len(series) > 0 else 0
                top_5.append({
                    "value": _sanitize_val(val),
                    "count": int(count),
                    "percentage": pct
                })

            mode_val = series.mode().iloc[0] if not series.mode().empty else None

            results["categorical_stats"][col] = {
                "count": int(len(non_null)),
                "null_count": int(series.isna().sum()),
                "unique_count": int(series.nunique(dropna=True)),
                "mode": _sanitize_val(mode_val),
                "top_frequencies": top_5,
            }

    return results
