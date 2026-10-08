import json
import math
import re
import time
from typing import Any, Optional
import numpy as np
import pandas as pd

from app.models.schemas import (
    DiscoveryFinding,
    DiscoveryResponse,
    DiscoverySummary,
)
from app.services.ai_agent import ai_agent
from app.services.dataset_store import dataset_store
from app.tools.profiling import _sanitize_val


def _calculate_pearson_p_value(r: float, n: int) -> float:
    """Calculates approximate two-tailed p-value for Pearson r using Fisher z-transform."""
    if n < 4 or abs(r) >= 1.0:
        return 0.0 if abs(r) >= 1.0 else 1.0
    try:
        # Fisher transformation: z = 0.5 * ln((1+r)/(1-r))
        z = 0.5 * math.log((1.0 + abs(r)) / (1.0 - abs(r)))
        se = 1.0 / math.sqrt(n - 3)
        z_stat = z / se
        # Standard normal CDF approximation via math.erf
        phi = 0.5 * (1.0 + math.erf(z_stat / math.sqrt(2.0)))
        p_val = 2.0 * (1.0 - phi)
        return max(0.0, min(1.0, float(p_val)))
    except Exception:
        return 0.05


class DiscoveryEngine:
    """Systematically discovers statistically meaningful relationships, differences,

    interactions, anomalies, and data-quality issues without requiring user questions.
    All numerical evidence is computed strictly via Python/Pandas.
    """

    def __init__(self, agent_service=None):
        self.agent_service = agent_service or ai_agent

    def discover(self, dataset_id: str, max_findings: int = 5) -> DiscoveryResponse:
        """Executes questionless discovery workflow:

        profile -> generate candidate findings -> rank -> LLM synthesis -> validated report.
        """
        start_time = time.perf_counter()
        df = dataset_store.get_dataset(dataset_id)
        if df is None:
            raise KeyError(f"Dataset with ID '{dataset_id}' not found.")

        meta = dataset_store.get_metadata(dataset_id) or {}
        filename = meta.get("filename", "dataset.csv")

        # 1. Profile and classify columns
        numeric_cols, categorical_cols, datetime_cols = self._classify_columns(df)

        # 2. Generate candidate findings across all discovery categories
        candidates: list[dict[str, Any]] = []

        # Category 1: Numeric Correlations
        candidates.extend(self._discover_correlations(df, numeric_cols))

        # Category 2: Group Differences
        candidates.extend(self._discover_group_differences(df, categorical_cols, numeric_cols))

        # Category 3: Category x Numeric Relationships
        candidates.extend(self._discover_category_numeric_relationships(df, categorical_cols, numeric_cols))

        # Category 4: Time Patterns
        if datetime_cols:
            candidates.extend(self._discover_time_patterns(df, datetime_cols, numeric_cols))

        # Category 5: Possible Interactions
        candidates.extend(self._discover_interactions(df, categorical_cols, numeric_cols))

        # Category 6: Data Quality Discoveries
        candidates.extend(self._discover_data_quality(df, numeric_cols))

        candidates_examined = len(candidates)

        # 3. Deterministic Ranking & Redundancy Filtering (BEFORE LLM)
        ranked_candidates = self._rank_candidates(candidates)
        top_candidates = ranked_candidates[:15]  # Send top 15 to reasoning layer

        # 4. LLM Ranking & Explanation with Candidate-ID Validation & Safe Fallback
        final_findings = self._synthesize_with_llm(
            filename=filename,
            top_candidates=top_candidates,
            max_findings=max_findings,
            total_rows=len(df),
            total_cols=len(df.columns),
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return DiscoveryResponse(
            dataset_id=dataset_id,
            filename=filename,
            summary=DiscoverySummary(
                rows=len(df),
                columns=len(df.columns),
                candidates_examined=candidates_examined,
                findings_returned=len(final_findings),
                execution_time_ms=elapsed_ms,
            ),
            findings=final_findings,
        )

    # -------------------------------------------------------------------------
    # Column Classification
    # -------------------------------------------------------------------------
    def _classify_columns(self, df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
        """Identifies usable numeric, categorical, and datetime columns."""
        numeric_cols = []
        categorical_cols = []
        datetime_cols = []

        for col in df.columns:
            series = df[col]
            non_null = series.dropna()
            if len(non_null) == 0:
                continue

            # Check Datetime
            if pd.api.types.is_datetime64_any_dtype(series):
                datetime_cols.append(col)
                continue

            # If string/object, test if it parses cleanly as datetime
            if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
                sample = non_null.head(50)
                try:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        parsed = pd.to_datetime(sample, errors="coerce")
                        if parsed.notna().sum() / len(sample) >= 0.8:
                            # Full parse check
                            full_parsed = pd.to_datetime(non_null, errors="coerce")
                            if full_parsed.notna().sum() / len(non_null) >= 0.7:
                                datetime_cols.append(col)
                                continue
                except Exception:
                    pass


            # Check Numeric
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                # Ensure non-trivial variance
                if len(non_null) > 1 and float(non_null.std(ddof=1)) > 1e-6:
                    numeric_cols.append(col)
                else:
                    # Constant or zero-variance numeric column
                    pass
                # Low-cardinality integer columns can also serve as categorical groupings (e.g. ratings 1-5, binary flags)
                if pd.api.types.is_integer_dtype(series) and 2 <= series.nunique(dropna=True) <= 8:
                    categorical_cols.append(col)
                continue


            # Check Categorical
            if not pd.api.types.is_numeric_dtype(series):
                n_unique = series.nunique(dropna=True)
                if 2 <= n_unique <= 25:
                    categorical_cols.append(col)

        return numeric_cols, categorical_cols, datetime_cols

    # -------------------------------------------------------------------------
    # 1. Numeric Correlations
    # -------------------------------------------------------------------------
    def _discover_correlations(self, df: pd.DataFrame, numeric_cols: list[str]) -> list[dict[str, Any]]:
        """Identifies strong and moderate pairwise correlations without duplication."""
        candidates = []
        cand_idx = 1

        n_cols = len(numeric_cols)
        if n_cols < 2:
            return candidates

        for i in range(n_cols):
            for j in range(i + 1, n_cols):
                col_a = numeric_cols[i]
                col_b = numeric_cols[j]

                paired = df[[col_a, col_b]].dropna()
                sample_size = len(paired)
                if sample_size < 5:
                    continue

                var_a = paired[col_a].var()
                var_b = paired[col_b].var()
                if var_a <= 1e-6 or var_b <= 1e-6:
                    continue

                r = float(paired[col_a].corr(paired[col_b]))
                if math.isnan(r) or math.isinf(r):
                    continue

                abs_r = abs(r)
                if abs_r < 0.25:
                    continue  # Ignore weak, negligible correlations

                direction = "Positive" if r > 0 else "Negative"
                if abs_r >= 0.7:
                    strength = "Strong"
                elif abs_r >= 0.4:
                    strength = "Moderate"
                else:
                    strength = "Weak"

                p_val = _calculate_pearson_p_value(r, sample_size)

                # Deterministic score
                score = abs_r * 40.0 + min(20.0, math.sqrt(sample_size)) + (10.0 if p_val < 0.01 else 0.0)

                verb = "moves together with" if r > 0 else "moves inversely with"
                candidates.append({
                    "id": f"corr_{cand_idx:03d}",
                    "type": "correlation",
                    "title": f"Strong Relationship: {col_a} ↔ {col_b}" if strength == "Strong" else f"Noticeable Relationship: {col_a} ↔ {col_b}",
                    "columns": [col_a, col_b],
                    "metric": {
                        "correlation": round(r, 4),
                        "direction": direction,
                        "strength": strength,
                        "sample_size": sample_size,
                        "p_value": round(p_val, 5),
                    },
                    "evidence": {
                        "column_a": col_a,
                        "column_b": col_b,
                        "correlation": round(r, 4),
                        "sample_size": sample_size,
                        "p_value": round(p_val, 5),
                        "direction": direction,
                        "strength": strength,
                        "description": f"Across {sample_size:,} records, {col_a} {verb} {col_b} (r = {r:.2f}, p < {max(0.001, p_val):.3f}).",
                    },
                    "explanation": f"{col_a} shows a statistically significant {strength.lower()} {direction.lower()} association with {col_b} in this dataset.",
                    "caution": f"This correlation indicates statistical association in this sample, but does not establish that {col_a} causes changes in {col_b}.",
                    "importance": "high" if strength == "Strong" else "medium",
                    "discovery_score": round(score, 2),
                })
                cand_idx += 1

        return candidates

    # -------------------------------------------------------------------------
    # 2. Group Differences
    # -------------------------------------------------------------------------
    def _discover_group_differences(
        self, df: pd.DataFrame, categorical_cols: list[str], numeric_cols: list[str]
    ) -> list[dict[str, Any]]:
        """Identifies categories whose subgroups substantially deviate from the overall average."""
        candidates = []
        cand_idx = 1
        min_group_size = max(4, int(len(df) * 0.05)) if len(df) >= 20 else 2

        for cat_col in categorical_cols:
            for num_col in numeric_cols:
                if cat_col == num_col:
                    continue
                sub_df = df[[cat_col, num_col]].dropna()
                if len(sub_df) < 10:
                    continue

                overall_mean = float(sub_df[num_col].mean())
                if abs(overall_mean) < 1e-6:
                    continue

                grouped = sub_df.groupby(cat_col, observed=True)[num_col]
                counts = grouped.count()
                means = grouped.mean()
                medians = grouped.median()

                for group_val, grp_count in counts.items():
                    if grp_count < min_group_size:
                        continue  # Avoid tiny groups

                    grp_mean = float(means[group_val])
                    grp_median = float(medians[group_val])
                    pct_diff = ((grp_mean - overall_mean) / abs(overall_mean)) * 100.0

                    if abs(pct_diff) >= 20.0:  # Meaningful divergence >= 20%
                        direction_word = "higher" if pct_diff > 0 else "lower"
                        score = min(35.0, abs(pct_diff) * 0.4) + min(25.0, math.sqrt(grp_count) * 3.0)


                        candidates.append({
                            "id": f"grp_{cand_idx:03d}",
                            "type": "group_difference",
                            "title": f"Unexpected Group Difference: {cat_col} = '{group_val}'",
                            "columns": [cat_col, num_col],
                            "metric": {
                                "group": str(group_val),
                                "group_mean": round(grp_mean, 2),
                                "overall_mean": round(overall_mean, 2),
                                "percentage_difference": round(pct_diff, 1),
                                "group_size": int(grp_count),
                            },
                            "evidence": {
                                "group_column": cat_col,
                                "group_value": str(group_val),
                                "metric_column": num_col,
                                "group_mean": round(grp_mean, 2),
                                "group_median": round(grp_median, 2),
                                "overall_mean": round(overall_mean, 2),
                                "percentage_difference": round(pct_diff, 1),
                                "group_size": int(grp_count),
                                "total_sample": len(sub_df),
                            },
                            "explanation": f"Records where {cat_col} is '{group_val}' average {abs(pct_diff):.1f}% {direction_word} {num_col} compared to the overall population mean.",
                            "caution": f"Group variations for '{group_val}' may be influenced by external confounders or subgroup selection factors.",
                            "importance": "high" if abs(pct_diff) >= 40.0 else "medium",
                            "discovery_score": round(score, 2),
                        })
                        cand_idx += 1

        return candidates

    # -------------------------------------------------------------------------
    # 3. Category x Numeric Relationships
    # -------------------------------------------------------------------------
    def _discover_category_numeric_relationships(
        self, df: pd.DataFrame, categorical_cols: list[str], numeric_cols: list[str]
    ) -> list[dict[str, Any]]:
        """Identifies categorical variables that create high outcome variance across categories."""
        candidates = []
        cand_idx = 1

        for cat_col in categorical_cols:
            for num_col in numeric_cols:
                if cat_col == num_col:
                    continue
                sub_df = df[[cat_col, num_col]].dropna()
                if len(sub_df) < 15:
                    continue


                grouped = sub_df.groupby(cat_col, observed=True)[num_col]
                valid_groups = [g for g, cnt in grouped.count().items() if cnt >= 3]
                if len(valid_groups) < 2:
                    continue

                group_means = grouped.mean().loc[valid_groups]
                overall_std = float(sub_df[num_col].std(ddof=1))
                if overall_std < 1e-6:
                    continue

                spread = float(group_means.max() - group_means.min())
                relative_spread = (spread / overall_std)

                if relative_spread >= 0.8:  # Spread across groups is >= 80% of total standard deviation
                    breakdown = {
                        str(g): {
                            "mean": round(float(grouped.mean().loc[g]), 2),
                            "count": int(grouped.count().loc[g]),
                        }
                        for g in valid_groups[:6]
                    }

                    score = min(35.0, relative_spread * 15.0) + min(15.0, len(valid_groups) * 3.0)

                    candidates.append({
                        "id": f"catnum_{cand_idx:03d}",
                        "type": "category_numeric",
                        "title": f"Outcome Divergence: {num_col} by {cat_col}",
                        "columns": [cat_col, num_col],
                        "metric": {
                            "spread": round(spread, 2),
                            "relative_spread_ratio": round(relative_spread, 2),
                            "groups_evaluated": len(valid_groups),
                        },
                        "evidence": {
                            "category_column": cat_col,
                            "metric_column": num_col,
                            "group_breakdown": breakdown,
                            "max_difference": round(spread, 2),
                            "standard_deviation": round(overall_std, 2),
                        },
                        "explanation": f"Average {num_col} shifts considerably across categories of {cat_col}, showing a maximum group difference of {spread:.2f}.",
                        "caution": "Categorical distributions may reflect operational segmentation rather than direct structural drivers.",
                        "importance": "high" if relative_spread >= 1.2 else "medium",
                        "discovery_score": round(score, 2),
                    })
                    cand_idx += 1

        return candidates

    # -------------------------------------------------------------------------
    # 4. Time Patterns
    # -------------------------------------------------------------------------
    def _discover_time_patterns(
        self, df: pd.DataFrame, datetime_cols: list[str], numeric_cols: list[str]
    ) -> list[dict[str, Any]]:
        """Identifies cyclical patterns across hour of day, day of week, or month."""
        candidates = []
        cand_idx = 1

        for dt_col in datetime_cols:
            parsed = pd.to_datetime(df[dt_col], errors="coerce")
            valid_dt_mask = parsed.notna()
            if valid_dt_mask.sum() < 15:
                continue

            dt_series = parsed[valid_dt_mask]
            temp_df = pd.DataFrame({"_dt": dt_series})

            temporal_dimensions = {}
            if dt_series.dt.hour.nunique() > 2:
                temporal_dimensions["hour"] = dt_series.dt.hour
            if dt_series.dt.day_name().nunique() > 2:
                temporal_dimensions["day_of_week"] = dt_series.dt.day_name()
            if dt_series.dt.month.nunique() > 2:
                temporal_dimensions["month"] = dt_series.dt.month_name()

            for dim_name, dim_series in temporal_dimensions.items():
                temp_df["_dim"] = dim_series
                for num_col in numeric_cols:
                    if num_col == dt_col:
                        continue
                    metric_series = df.loc[valid_dt_mask, num_col].dropna()
                    shared_idx = temp_df.index.intersection(metric_series.index)
                    if len(shared_idx) < 15:
                        continue

                    eval_df = pd.DataFrame({
                        "dim": temp_df.loc[shared_idx, "_dim"],
                        "val": metric_series.loc[shared_idx],
                    })

                    grouped = eval_df.groupby("dim", observed=True)["val"]
                    counts = grouped.count()
                    valid_segs = [s for s, c in counts.items() if c >= 3]
                    if len(valid_segs) < 2:
                        continue

                    means = grouped.mean().loc[valid_segs]
                    overall_mean = float(eval_df["val"].mean())
                    if abs(overall_mean) < 1e-6:
                        continue

                    spread = float(means.max() - means.min())
                    pct_spread = (spread / abs(overall_mean)) * 100.0

                    if pct_spread >= 25.0:  # Noticeable cycle deviation >= 25%
                        peak_seg = str(means.idxmax())
                        peak_val = float(means.max())
                        low_seg = str(means.idxmin())
                        low_val = float(means.min())

                        score = min(35.0, pct_spread * 0.4) + 15.0

                        candidates.append({
                            "id": f"time_{cand_idx:03d}",
                            "type": "time_pattern",
                            "title": f"Cyclical Time Pattern: {num_col} by {dim_name.replace('_', ' ').title()}",
                            "columns": [dt_col, num_col],
                            "metric": {
                                "temporal_unit": dim_name,
                                "peak_segment": peak_seg,
                                "peak_mean": round(peak_val, 2),
                                "trough_segment": low_seg,
                                "trough_mean": round(low_val, 2),
                                "spread_percentage": round(pct_spread, 1),
                            },
                            "evidence": {
                                "datetime_column": dt_col,
                                "temporal_unit": dim_name,
                                "peak": {"segment": peak_seg, "mean": round(peak_val, 2)},
                                "trough": {"segment": low_seg, "mean": round(low_val, 2)},
                                "segment_means": {str(k): round(float(v), 2) for k, v in means.items()},
                            },
                            "explanation": f"{num_col} exhibits cyclical differences across {dim_name.replace('_', ' ')}, peaking at '{peak_seg}' ({peak_val:.2f}) and dipping at '{low_seg}' ({low_val:.2f}).",
                            "caution": "Time-based patterns can be sensitive to reporting schedules, holidays, or seasonal artifacts.",
                            "importance": "medium",
                            "discovery_score": round(score, 2),
                        })
                        cand_idx += 1

        return candidates

    # -------------------------------------------------------------------------
    # 5. Possible Interactions
    # -------------------------------------------------------------------------
    def _discover_interactions(
        self, df: pd.DataFrame, categorical_cols: list[str], numeric_cols: list[str]
    ) -> list[dict[str, Any]]:
        """Identifies pairs of categorical features that exhibit non-additive interactions on numeric outcomes."""
        candidates = []
        cand_idx = 1

        # Use compact categorical columns (2 to 4 unique values)
        compact_cats = [c for c in categorical_cols if 2 <= df[c].nunique(dropna=True) <= 4]
        if len(compact_cats) < 2 or not numeric_cols:
            return candidates

        for i in range(len(compact_cats)):
            for j in range(i + 1, len(compact_cats)):
                c1 = compact_cats[i]
                c2 = compact_cats[j]

                for num_col in numeric_cols:
                    if num_col in (c1, c2):
                        continue
                    sub_df = df[[c1, c2, num_col]].dropna()
                    if len(sub_df) < 20:
                        continue


                    # Compute 2-way cell means
                    grouped = sub_df.groupby([c1, c2], observed=True)[num_col]
                    counts = grouped.count()
                    if (counts < 3).any() or len(counts) < 4:
                        continue  # Cell sizes too small

                    cell_means = grouped.mean()
                    grand_mean = float(sub_df[num_col].mean())
                    overall_std = float(sub_df[num_col].std(ddof=1))
                    if overall_std < 1e-6:
                        continue

                    c1_means = sub_df.groupby(c1, observed=True)[num_col].mean()
                    c2_means = sub_df.groupby(c2, observed=True)[num_col].mean()

                    # Compute additive expectation: E_ij = mean_i + mean_j - grand_mean
                    max_residual = 0.0
                    cell_evidence = {}
                    for (v1, v2), actual_cell in cell_means.items():
                        expected = float(c1_means[v1] + c2_means[v2] - grand_mean)
                        res = abs(float(actual_cell) - expected)
                        cell_evidence[f"{v1} + {v2}"] = {
                            "actual_mean": round(float(actual_cell), 2),
                            "additive_expected": round(expected, 2),
                            "interaction_delta": round(res, 2),
                        }
                        if res > max_residual:
                            max_residual = res

                    interaction_ratio = max_residual / overall_std
                    if interaction_ratio >= 0.45:  # Noticeable interaction deviation
                        score = min(35.0, interaction_ratio * 20.0) + 12.0
                        candidates.append({
                            "id": f"inter_{cand_idx:03d}",
                            "type": "interaction",
                            "title": f"Possible Interaction: {c1} + {c2} on {num_col}",
                            "columns": [c1, c2, num_col],
                            "metric": {
                                "interaction_effect_ratio": round(interaction_ratio, 2),
                                "max_deviation": round(max_residual, 2),
                            },
                            "evidence": {
                                "factors": [c1, c2],
                                "metric_column": num_col,
                                "cells": cell_evidence,
                            },
                            "explanation": f"The relationship between {c1} and {num_col} varies depending on {c2}, departing from a simple additive pattern.",
                            "caution": "Interaction effects suggest combined influences, but require domain testing to verify underlying mechanisms.",
                            "importance": "medium",
                            "discovery_score": round(score, 2),
                        })
                        cand_idx += 1

        return candidates

    # -------------------------------------------------------------------------
    # 6. Data Quality Discoveries
    # -------------------------------------------------------------------------
    def _discover_data_quality(self, df: pd.DataFrame, numeric_cols: list[str]) -> list[dict[str, Any]]:
        """Flags potential data quality issues: high missingness, constant columns, duplicate variables, outliers."""
        candidates = []
        cand_idx = 1
        total_rows = len(df)

        if total_rows == 0:
            return candidates

        # A. High Missingness
        for col in df.columns:
            null_count = int(df[col].isna().sum())
            null_pct = round((null_count / total_rows) * 100.0, 1)
            if null_pct >= 25.0:
                score = 50.0 + min(25.0, null_pct * 0.5)
                candidates.append({
                    "id": f"dq_null_{cand_idx:03d}",
                    "type": "data_quality",
                    "title": f"Possible Data Quality Issue: High Missingness in '{col}'",
                    "columns": [col],
                    "metric": {
                        "missing_percentage": null_pct,
                        "missing_rows": null_count,
                        "total_rows": total_rows,
                    },
                    "evidence": {
                        "column": col,
                        "missing_count": null_count,
                        "missing_percentage": null_pct,
                        "total_rows": total_rows,
                    },
                    "explanation": f"Column '{col}' is missing in {null_pct}% of records ({null_count:,} out of {total_rows:,} rows).",
                    "caution": "High missingness can create survivorship bias or undermine conclusions drawn from this feature.",
                    "importance": "high" if null_pct >= 50.0 else "medium",
                    "discovery_score": round(score, 2),
                })
                cand_idx += 1

        # B. Constant Columns
        for col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0 and non_null.nunique() == 1:
                const_val = _sanitize_val(non_null.iloc[0])
                candidates.append({
                    "id": f"dq_const_{cand_idx:03d}",
                    "type": "data_quality",
                    "title": f"Possible Data Quality Issue: Constant Feature '{col}'",
                    "columns": [col],
                    "metric": {
                        "unique_count": 1,
                        "constant_value": str(const_val),
                    },
                    "evidence": {
                        "column": col,
                        "unique_count": 1,
                        "value": const_val,
                    },
                    "explanation": f"Column '{col}' contains only a single constant value ('{const_val}') across all non-null entries.",
                    "caution": "Constant variables carry zero variance and provide no analytical or discriminatory signal.",
                    "importance": "high",
                    "discovery_score": 75.0,
                })
                cand_idx += 1

        # C. Identical or Redundant Columns
        col_list = list(df.columns)
        for i in range(len(col_list)):
            for j in range(i + 1, len(col_list)):
                c1 = col_list[i]
                c2 = col_list[j]
                if df[c1].equals(df[c2]):
                    candidates.append({
                        "id": f"dq_dup_{cand_idx:03d}",
                        "type": "data_quality",
                        "title": f"Possible Data Quality Issue: Identical Columns '{c1}' & '{c2}'",
                        "columns": [c1, c2],
                        "metric": {"is_exact_duplicate": True},
                        "evidence": {"column_1": c1, "column_2": c2, "identical": True},
                        "explanation": f"Columns '{c1}' and '{c2}' have 100% identical values across all rows, indicating redundant data.",
                        "caution": "One of these columns may be redundant or an unversioned copy of the other.",
                        "importance": "high",
                        "discovery_score": 72.0,
                    })
                    cand_idx += 1


        # D. Extreme Statistical Outliers
        for num_col in numeric_cols:
            series = df[num_col].dropna()
            if len(series) >= 10:
                q25 = float(series.quantile(0.25))
                q75 = float(series.quantile(0.75))
                iqr = q75 - q25
                if iqr > 1e-6:
                    upper = q75 + 3.0 * iqr  # Strict 3x IQR extreme outlier check
                    lower = q25 - 3.0 * iqr
                    outliers = series[(series < lower) | (series > upper)]
                    outlier_count = len(outliers)
                    outlier_pct = round((outlier_count / len(series)) * 100.0, 1)

                    if outlier_pct >= 2.0:
                        score = 50.0 + min(25.0, outlier_pct * 3.0)
                        candidates.append({
                            "id": f"dq_outlier_{cand_idx:03d}",
                            "type": "data_quality",
                            "title": f"Potential Outliers: Extreme Values in '{num_col}'",
                            "columns": [num_col],
                            "metric": {
                                "outlier_count": outlier_count,
                                "outlier_percentage": outlier_pct,
                                "threshold_multiplier": 3.0,
                            },
                            "evidence": {
                                "column": num_col,
                                "extreme_outliers": outlier_count,
                                "percentage": outlier_pct,
                                "iqr_bounds": {"lower": round(lower, 2), "upper": round(upper, 2)},
                                "sample_extreme_values": [_sanitize_val(v) for v in outliers.head(3)],
                            },
                            "explanation": f"Detected {outlier_count} extreme outlier observations ({outlier_pct}% of values) in '{num_col}' falling outside extreme IQR thresholds.",
                            "caution": "Extreme records may represent data entry anomalies, measurement artifacts, or valid high-impact events.",
                            "importance": "medium",
                            "discovery_score": round(score, 2),
                        })
                        cand_idx += 1

        return candidates

    # -------------------------------------------------------------------------
    # Deterministic Candidate Ranking & Redundancy Filter
    # -------------------------------------------------------------------------
    def _rank_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Ranks candidate findings deterministically using discovery score and category diversity interleaving."""
        if not candidates:
            return []

        # Sort initially by raw discovery score descending
        sorted_cand = sorted(candidates, key=lambda c: c.get("discovery_score", 0.0), reverse=True)

        # Apply redundancy penalty if exact same column pair already included
        seen_pairs: set[frozenset] = set()
        adjusted: list[dict[str, Any]] = []
        for item in sorted_cand:
            cols = item.get("columns", [])
            pair_key = frozenset(cols[:2]) if len(cols) >= 2 else frozenset(cols)
            score = item.get("discovery_score", 0.0)
            if pair_key in seen_pairs:
                score *= 0.65
            item["discovery_score"] = round(score, 2)
            seen_pairs.add(pair_key)
            adjusted.append(item)

        # Group by category type
        by_type: dict[str, list[dict[str, Any]]] = {}
        for item in adjusted:
            t = item.get("type", "other")
            by_type.setdefault(t, []).append(item)

        # Sort each type's candidates by score
        for t in by_type:
            by_type[t].sort(key=lambda c: c.get("discovery_score", 0.0), reverse=True)

        # Interleave across discovery types in priority order
        priority_order = [
            "correlation",
            "group_difference",
            "interaction",
            "time_pattern",
            "data_quality",
            "category_numeric",
        ]

        ranked: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        # Pass 1: Ensure top 3 from each category are promoted
        for pass_round in range(3):

            for cat_type in priority_order:
                cat_list = by_type.get(cat_type, [])
                if len(cat_list) > pass_round:
                    cand = cat_list[pass_round]
                    if cand["id"] not in seen_ids:
                        ranked.append(cand)
                        seen_ids.add(cand["id"])

        # Pass 2: Fill remainder ordered by discovery score
        adjusted.sort(key=lambda c: c.get("discovery_score", 0.0), reverse=True)
        for item in adjusted:
            if item["id"] not in seen_ids:
                ranked.append(item)
                seen_ids.add(item["id"])

        return ranked


    # -------------------------------------------------------------------------
    # LLM Ranking & Explanation Synthesis Layer
    # -------------------------------------------------------------------------
    def _synthesize_with_llm(
        self,
        filename: str,
        top_candidates: list[dict[str, Any]],
        max_findings: int,
        total_rows: int,
        total_cols: int,
    ) -> list[DiscoveryFinding]:
        """Sends top candidate statistical evidence to LLM reasoning layer to select and explain findings.

        Validates all candidate IDs and falls back cleanly to deterministic outputs if LLM fails.
        """
        if not top_candidates:
            return []

        candidate_map = {c["id"]: c for c in top_candidates}

        # Prepare payload for LLM prompt
        prompt_candidates = []
        for c in top_candidates:
            prompt_candidates.append({
                "candidate_id": c["id"],
                "type": c["type"],
                "columns": c["columns"],
                "metric": c["metric"],
                "calculated_evidence": c["evidence"].get("description") or c["explanation"],
            })

        system_instruction = (
            "You are DataPilot's Discovery Reasoning Layer.\n"
            "Your role is to analyze pre-calculated statistical candidate discoveries and select the most insightful findings for the user.\n\n"
            "STRICT RULES:\n"
            "1. Output valid JSON ONLY. No markdown conversational filler.\n"
            "2. You MUST ONLY reference candidate_ids from the provided candidates list. NEVER invent candidate IDs.\n"
            "3. DO NOT calculate or invent numerical statistics. The Python analysis layer is the single source of truth.\n"
            "4. NEVER claim causation (do not say 'X causes Y'; use 'is associated with', 'moves together with', 'shows difference across').\n"
            "5. Select the top most valuable discoveries (up to the requested count).\n"
            "6. Provide a concise, clear explanation of why each finding matters.\n\n"
            "OUTPUT JSON FORMAT:\n"
            "{\n"
            '  "selected_findings": [\n'
            "    {\n"
            '      "candidate_id": "corr_001",\n'
            '      "title": "Strong Positive Relationship Between Age and Purchase Amount",\n'
            '      "importance": "high",\n'
            '      "explanation": "Older customers tend to have higher purchase amounts across this dataset.",\n'
            '      "caution": "This correlation does not establish that age causes higher purchases."\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Dataset: '{filename}' ({total_rows:,} rows, {total_cols} columns)\n"
            f"Select up to {max_findings} most valuable discoveries from these verified candidate findings:\n\n"
            f"{json.dumps(prompt_candidates, indent=2)}\n"
        )

        llm_findings = []
        try:
            raw_text = self.agent_service.provider.generate_text(
                prompt=user_prompt,
                system_instruction=system_instruction,
            )
            llm_findings = self._parse_and_validate_llm_response(raw_text, candidate_map, max_findings)
        except Exception:
            # Fall back cleanly if provider raises or fails
            llm_findings = []

        # If LLM returned valid selections, return them
        if llm_findings:
            return llm_findings

        # Fallback cleanly to deterministic selections
        return self._deterministic_fallback_findings(top_candidates[:max_findings])

    def _parse_and_validate_llm_response(
        self, raw_text: str, candidate_map: dict[str, dict[str, Any]], max_findings: int
    ) -> list[DiscoveryFinding]:
        """Parses LLM JSON and validates candidate IDs against candidate_map."""
        if not raw_text or not raw_text.strip():
            return []

        # Clean potential markdown fences ```json ... ```
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except Exception:
            # Attempt to extract JSON substring
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    return []
            else:
                return []

        selected = data.get("selected_findings", [])
        if not isinstance(selected, list):
            return []

        validated: list[DiscoveryFinding] = []
        seen_ids = set()

        for item in selected:
            if not isinstance(item, dict):
                continue
            cand_id = item.get("candidate_id")
            # Strict candidate-ID validation: MUST exist in candidate_map
            if not cand_id or cand_id not in candidate_map or cand_id in seen_ids:
                continue

            orig = candidate_map[cand_id]
            seen_ids.add(cand_id)

            title = item.get("title") or orig["title"]
            importance = str(item.get("importance", orig["importance"])).lower()
            if importance not in ("high", "medium", "low"):
                importance = orig["importance"]
            explanation = item.get("explanation") or orig["explanation"]
            caution = item.get("caution") or orig.get("caution")

            validated.append(
                DiscoveryFinding(
                    id=cand_id,
                    type=orig["type"],
                    title=title,
                    columns=orig["columns"],
                    metric=orig["metric"],
                    evidence=orig["evidence"],
                    explanation=explanation,
                    caution=caution,
                    importance=importance,
                    discovery_score=orig.get("discovery_score", 0.0),
                )
            )

            if len(validated) >= max_findings:
                break

        return validated

    def _deterministic_fallback_findings(self, top_candidates: list[dict[str, Any]]) -> list[DiscoveryFinding]:
        """Generates deterministic validated findings directly from calculated statistical evidence."""
        findings = []
        for c in top_candidates:
            findings.append(
                DiscoveryFinding(
                    id=c["id"],
                    type=c["type"],
                    title=c["title"],
                    columns=c["columns"],
                    metric=c["metric"],
                    evidence=c["evidence"],
                    explanation=c["explanation"],
                    caution=c.get("caution"),
                    importance=c.get("importance", "medium"),
                    discovery_score=c.get("discovery_score", 0.0),
                )
            )
        return findings


discovery_engine = DiscoveryEngine()
