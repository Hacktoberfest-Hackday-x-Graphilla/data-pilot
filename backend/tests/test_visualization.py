import numpy as np
import pandas as pd
import pytest
from app.services.dataset_store import dataset_store
from app.services.discovery_engine import DiscoveryEngine
from app.models.schemas import VisualizationSpec

@pytest.fixture(autouse=True)
def clean_store():
    dataset_store.clear()
    yield
    dataset_store.clear()

def test_correlation_visualization():
    df = pd.DataFrame({
        "units": [10, 20, 30, 40, 50, 60],
        "sales": [100.0, 205.0, 298.0, 410.0, 495.0, 610.0],
    })
    summary = dataset_store.add_dataset(df, filename="corr.csv")
    engine = DiscoveryEngine()
    res = engine.discover(summary.dataset_id, max_findings=5)

    corr_findings = [f for f in res.findings if f.type == "correlation"]
    assert len(corr_findings) >= 1
    f = corr_findings[0]
    assert f.visualization is not None
    assert isinstance(f.visualization, VisualizationSpec)
    assert f.visualization.chart_type == "scatter"
    assert f.visualization.x_key == "units"
    assert f.visualization.y_key == "sales"
    assert len(f.visualization.data) == 6
    assert f.visualization.data[0]["units"] == 10
    assert f.visualization.data[0]["sales"] == 100.0

def test_group_difference_visualization():
    # Group difference produces bar chart and plotted values match backend group means
    df = pd.DataFrame({
        "region": ["East"] * 20 + ["West"] * 20 + ["North"] * 20,
        "discount": [0.25] * 20 + [0.05] * 20 + [0.15] * 20,
    })
    summary = dataset_store.add_dataset(df, filename="groups.csv")
    engine = DiscoveryEngine()
    res = engine.discover(summary.dataset_id, max_findings=5)

    grp_findings = [f for f in res.findings if f.type == "group_difference"]
    assert len(grp_findings) >= 1
    f = grp_findings[0]
    assert f.visualization is not None
    assert f.visualization.chart_type == "bar"
    assert f.visualization.x_key == "region"
    assert f.visualization.y_key == "discount"

    # Plotted values must match backend-calculated group means
    data_map = {item["region"]: item["discount"] for item in f.visualization.data}
    assert pytest.approx(data_map["East"], 0.01) == 0.25
    assert pytest.approx(data_map["West"], 0.01) == 0.05
    assert pytest.approx(data_map["North"], 0.01) == 0.15
    if "group" in f.metric and "group_mean" in f.metric:
        assert data_map[f.metric["group"]] == f.metric["group_mean"]

def test_time_pattern_visualization():
    # Time pattern produces line chart and points are ordered chronologically
    hours = [9, 14, 20] * 10
    dates = [f"2026-03-15 {h:02d}:00:00" for h in hours]
    sales = [100.0 if h == 20 else 40.0 for h in hours]
    df = pd.DataFrame({"order_time": dates, "sales": sales})
    summary = dataset_store.add_dataset(df, filename="time.csv")
    engine = DiscoveryEngine()
    res = engine.discover(summary.dataset_id, max_findings=5)

    time_findings = [f for f in res.findings if f.type == "time_pattern"]
    assert len(time_findings) >= 1
    f = time_findings[0]
    assert f.visualization is not None
    assert f.visualization.chart_type == "line"

    # Check chronological ordering
    x_key = f.visualization.x_key
    points = [int(p[x_key]) for p in f.visualization.data if str(p[x_key]).isdigit()]
    assert points == sorted(points)

def test_large_dataset_bounded_and_deterministic():
    # 2000 rows dataset: full dataset used for stats, but chart data bounded and deterministic
    n = 2000
    np.random.seed(42)
    units = np.arange(n)
    sales = units * 3.5 + np.random.normal(0, 10, n)
    df = pd.DataFrame({"units": units, "sales": sales})
    summary = dataset_store.add_dataset(df, filename="large.csv")
    engine = DiscoveryEngine()

    res1 = engine.discover(summary.dataset_id, max_findings=5)
    f1 = next(f for f in res1.findings if f.type == "correlation")
    assert f1.metric["sample_size"] == n  # Full dataset used for statistics
    assert len(f1.visualization.data) <= 450  # Bounded data points for charting
    assert len(f1.visualization.data) >= 300

    res2 = engine.discover(summary.dataset_id, max_findings=5)
    f2 = next(f for f in res2.findings if f.type == "correlation")
    assert f1.visualization.data == f2.visualization.data

def test_data_quality_visualization_is_null():
    # Constant column should return visualization = None
    df = pd.DataFrame({"constant_col": ["SAME"] * 50, "other": list(range(50))})
    summary = dataset_store.add_dataset(df, filename="dq.csv")
    engine = DiscoveryEngine()
    res = engine.discover(summary.dataset_id, max_findings=5)

    dq_findings = [f for f in res.findings if f.type == "data_quality"]
    assert len(dq_findings) >= 1
    const_f = next((f for f in dq_findings if "constant_col" in f.columns), None)
    assert const_f is not None
    assert const_f.visualization is None
