from typing import Any, Optional
import numpy as np
import pandas as pd
from app.tools.profiling import _sanitize_val

def detect_anomalies(
    df: pd.DataFrame,
    columns: Optional[Any] = None,
    method: str = "iqr",
    threshold: Optional[float] = None,
    **kwargs: Any
) -> dict[str, Any]:
    """Detects statistical outliers in numerical features using IQR or Z-score methods."""
    method = method.lower()
    if method not in ("iqr", "zscore"):
        raise ValueError("Method must be either 'iqr' or 'zscore'.")

    cols = columns if columns is not None else kwargs.get("column")
    if isinstance(cols, str):
        cols = [cols]

    # Select numerical columns
    if cols:
        valid_cols = [c for c in cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    else:
        valid_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])]

    if not valid_cols:
        raise ValueError("No valid numerical columns available for anomaly detection.")

    if threshold is None:
        threshold = 1.5 if method == "iqr" else 3.0

    anomalies_by_column = {}
    total_rows = len(df)

    for col in valid_cols:
        series = df[col].dropna()
        if len(series) < 4:
            anomalies_by_column[col] = {
                "outlier_count": 0,
                "outlier_percentage": 0.0,
                "note": "Insufficient data points (< 4).",
            }
            continue

        if method == "iqr":
            q25 = float(series.quantile(0.25))
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25
            lower_bound = q25 - (threshold * iqr)
            upper_bound = q75 + (threshold * iqr)
            outlier_mask = (series < lower_bound) | (series > upper_bound)
            bounds = {"lower": _sanitize_val(lower_bound), "upper": _sanitize_val(upper_bound)}
        else: # zscore
            mean = float(series.mean())
            std = float(series.std(ddof=1))
            if std == 0:
                outlier_mask = pd.Series(False, index=series.index)
                bounds = {"lower": _sanitize_val(mean), "upper": _sanitize_val(mean)}
            else:
                z_scores = np.abs((series - mean) / std)
                outlier_mask = z_scores > threshold
                bounds = {
                    "lower": _sanitize_val(mean - threshold * std),
                    "upper": _sanitize_val(mean + threshold * std),
                }

        outliers = series[outlier_mask]
        count = int(len(outliers))
        pct = round(count / total_rows * 100.0, 2) if total_rows > 0 else 0.0

        sample_outliers = []
        for idx, val in outliers.head(5).items():
            sample_outliers.append({
                "row_index": int(idx),
                "value": _sanitize_val(val),
            })

        anomalies_by_column[col] = {
            "method": method,
            "threshold": threshold,
            "bounds": bounds,
            "outlier_count": count,
            "outlier_percentage": pct,
            "sample_outliers": sample_outliers,
        }

    return {
        "detection_method": method,
        "columns_analyzed": valid_cols,
        "total_rows": total_rows,
        "anomalies": anomalies_by_column,
    }
