from typing import Any
import numpy as np
import pandas as pd

def _get_column_category(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        return "numeric"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    elif pd.api.types.is_bool_dtype(series):
        return "boolean"
    else:
        return "categorical"

def _sanitize_val(val: Any) -> Any:
    if pd.isna(val):
        return None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        if np.isneginf(val) or np.isposinf(val) or np.isnan(val):
            return None
        return round(float(val), 4)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    return str(val)

def profile_dataset(df: pd.DataFrame) -> dict[str, Any]:
    """Generates a comprehensive dataset profile including dimensions, types, missing values, and samples."""
    total_rows = len(df)
    total_cols = len(df.columns)
    memory_mb = round(float(df.memory_usage(deep=True).sum()) / (1024 * 1024), 3)
    duplicates = int(df.duplicated().sum()) if total_rows > 0 else 0

    columns_profile = []
    numeric_cols = []
    categorical_cols = []

    for col in df.columns:
        series = df[col]
        cat = _get_column_category(series)
        null_count = int(series.isna().sum())
        null_pct = round((null_count / total_rows * 100.0), 2) if total_rows > 0 else 0.0
        unique_cnt = int(series.nunique(dropna=True))

        non_null_samples = series.dropna().unique()[:4]
        samples = [_sanitize_val(v) for v in non_null_samples]

        if cat == "numeric":
            numeric_cols.append(str(col))
        elif cat == "categorical":
            categorical_cols.append(str(col))

        columns_profile.append({
            "name": str(col),
            "dtype": str(series.dtype),
            "category": cat,
            "null_count": null_count,
            "null_percentage": null_pct,
            "unique_count": unique_cnt,
            "sample_values": samples,
        })

    # Prepare head samples (5 rows)
    head_df = df.head(5)
    sample_rows = []
    for _, row in head_df.iterrows():
        sample_rows.append({str(k): _sanitize_val(v) for k, v in row.to_dict().items()})

    return {
        "row_count": total_rows,
        "column_count": total_cols,
        "memory_mb": memory_mb,
        "duplicate_rows": duplicates,
        "columns": columns_profile,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "sample_rows": sample_rows,
    }
