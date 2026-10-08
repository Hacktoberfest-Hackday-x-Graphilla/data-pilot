import numpy as np
import pandas as pd
import pytest

from app.tools.profiling import profile_dataset
from app.tools.statistics import calculate_statistics
from app.tools.comparisons import group_and_compare
from app.tools.anomalies import detect_anomalies
from app.tools.charts import create_chart
from app.tools.correlations import find_correlations

@pytest.fixture
def sample_df():
    """Generates a representative e-commerce dataset with outliers and missing values."""
    np.random.seed(42)
    data = {
        "product": ["Widget A", "Widget B", "Gadget X", "Gadget Y", "Device 1", "Device 2", "Widget C", "Gadget Z"],
        "category": ["Widgets", "Widgets", "Gadgets", "Gadgets", "Devices", "Devices", "Widgets", "Gadgets"],
        "price": [10.5, 25.0, 150.0, 180.0, 45.0, 60.0, 12.0, 2000.0],  # 2000.0 is an outlier
        "units_sold": [100, 80, 25, 20, 50, 45, 120, 2],
        "customer_rating": [4.5, 3.8, 4.9, 4.2, np.nan, 3.5, 4.0, 2.0],  # contains NaN
        "is_active": [True, True, True, True, False, True, True, False],
    }
    return pd.DataFrame(data)

def test_profile_dataset(sample_df):
    profile = profile_dataset(sample_df)
    assert profile["row_count"] == 8
    assert profile["column_count"] == 6
    assert profile["duplicate_rows"] == 0
    assert "price" in profile["numeric_columns"]
    assert "category" in profile["categorical_columns"]
    assert len(profile["sample_rows"]) == 5
    
    # Check rating column missing value detection
    rating_col = next(c for c in profile["columns"] if c["name"] == "customer_rating")
    assert rating_col["null_count"] == 1
    assert rating_col["null_percentage"] == 12.5

def test_calculate_statistics(sample_df):
    stats = calculate_statistics(sample_df, columns=["price", "category"])
    # Numeric checks
    price_stats = stats["numeric_stats"]["price"]
    assert price_stats["count"] == 8
    assert price_stats["min"] == 10.5
    assert price_stats["max"] == 2000.0
    assert price_stats["mean"] > 0
    
    # Categorical checks
    cat_stats = stats["categorical_stats"]["category"]
    assert cat_stats["unique_count"] == 3
    assert len(cat_stats["top_frequencies"]) == 3

def test_group_and_compare(sample_df):
    comp = group_and_compare(
        sample_df,
        group_by="category",
        metric_columns=["price", "units_sold"],
        aggregations=["mean", "sum"]
    )
    assert comp["group_by"] == "category"
    assert comp["total_groups"] == 3
    assert len(comp["results"]) == 3
    
    # Each group should have aggregated values
    for row in comp["results"]:
        assert "group" in row
        assert "price_mean" in row
        assert "units_sold_sum" in row

def test_detect_anomalies_iqr(sample_df):
    result = detect_anomalies(sample_df, columns=["price"], method="iqr", threshold=1.5)
    price_anomalies = result["anomalies"]["price"]
    assert price_anomalies["outlier_count"] >= 1
    assert any(o["value"] == 2000.0 for o in price_anomalies["sample_outliers"])

def test_detect_anomalies_zscore(sample_df):
    result = detect_anomalies(sample_df, columns=["price"], method="zscore", threshold=2.0)
    price_anomalies = result["anomalies"]["price"]
    assert price_anomalies["outlier_count"] >= 1

def test_create_chart_bar(sample_df):
    chart = create_chart(sample_df, chart_type="bar", x="category", y="units_sold", aggregation="sum")
    assert chart["chart_type"] == "bar"
    assert len(chart["data"]) == 3
    assert all("x" in d and "y" in d for d in chart["data"])

def test_create_chart_scatter(sample_df):
    chart = create_chart(sample_df, chart_type="scatter", x="price", y="units_sold")
    assert chart["chart_type"] == "scatter"
    assert len(chart["data"]) == 8

def test_create_chart_box(sample_df):
    chart = create_chart(sample_df, chart_type="box", x="price")
    assert chart["chart_type"] == "box"
    assert len(chart["data"]) == 1
    box_data = chart["data"][0]
    assert "q25" in box_data
    assert "median" in box_data
    assert "q75" in box_data

def test_find_correlations(sample_df):
    result = find_correlations(sample_df, columns=["price", "units_sold"], method="pearson")
    assert result["method"] == "pearson"
    assert "matrix" in result
    assert "price" in result["matrix"]
    assert "units_sold" in result["matrix"]["price"]
    # Top pairs
    assert len(result["top_correlated_pairs"]) >= 1
    pair = result["top_correlated_pairs"][0]
    assert pair["feature_1"] == "price"
    assert pair["feature_2"] == "units_sold"
    # Price is negatively correlated with units_sold in this dataset
    assert pair["correlation"] < 0
