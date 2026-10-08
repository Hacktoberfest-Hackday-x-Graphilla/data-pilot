from typing import Any, Optional
import numpy as np
import pandas as pd
from app.tools.profiling import _sanitize_val

def find_correlations(
    df: pd.DataFrame,
    columns: Optional[Any] = None,
    method: str = "pearson",
    min_threshold: Optional[float] = None,
    **kwargs: Any
) -> dict[str, Any]:
    """Computes correlation matrix and identifies the strongest pairwise relationships."""
    method = method.lower()
    if method not in ("pearson", "spearman", "kendall"):
        raise ValueError("Method must be 'pearson', 'spearman', or 'kendall'.")

    cols = columns if columns is not None else kwargs.get("column")
    if isinstance(cols, str):
        cols = [cols]

    # Select numerical columns
    if cols:
        valid_cols = [c for c in cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    else:
        valid_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])]

    thresh = min_threshold if min_threshold is not None else kwargs.get("threshold", 0.0)
    min_threshold = float(thresh)

    if len(valid_cols) < 2:
        raise ValueError("Correlation analysis requires at least 2 numerical columns.")

    numeric_df = df[valid_cols].dropna(how="all")
    corr_matrix = numeric_df.corr(method=method)

    matrix_dict = {}
    pairs = []

    cols = list(corr_matrix.columns)
    for i, col1 in enumerate(cols):
        matrix_dict[col1] = {}
        for j, col2 in enumerate(cols):
            val = corr_matrix.loc[col1, col2]
            matrix_dict[col1][col2] = _sanitize_val(val)
            if i < j and not pd.isna(val):
                pairs.append({
                    "feature_1": col1,
                    "feature_2": col2,
                    "correlation": round(float(val), 4),
                    "abs_correlation": round(abs(float(val)), 4),
                })

    # Filter and sort
    filtered_pairs = [p for p in pairs if p["abs_correlation"] >= min_threshold]
    filtered_pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)

    positive_corr = sorted([p for p in filtered_pairs if p["correlation"] > 0], key=lambda x: x["correlation"], reverse=True)
    negative_corr = sorted([p for p in filtered_pairs if p["correlation"] < 0], key=lambda x: x["correlation"])

    return {
        "method": method,
        "features": valid_cols,
        "matrix": matrix_dict,
        "top_correlated_pairs": filtered_pairs[:10],
        "top_positive": positive_corr[:5],
        "top_negative": negative_corr[:5],
    }
