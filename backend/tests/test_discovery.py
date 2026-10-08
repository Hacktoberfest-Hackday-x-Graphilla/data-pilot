import io
import json
from unittest.mock import MagicMock
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.dataset_store import dataset_store
from app.services.discovery_engine import DiscoveryEngine, discovery_engine
from app.services.providers.base import BaseLLMProvider

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_store():
    dataset_store.clear()
    yield
    dataset_store.clear()


@pytest.fixture(autouse=True)
def mock_default_llm(monkeypatch):
    """Ensures unit tests run 100% offline and do not depend on external live LLM APIs."""
    from app.services.ai_agent import ai_agent
    mock_provider = MagicMock(spec=BaseLLMProvider)
    mock_provider.provider_name = "mock_provider"
    mock_provider.generate_text.return_value = ""
    monkeypatch.setattr(ai_agent, "provider", mock_provider)
    monkeypatch.setattr(discovery_engine.agent_service, "provider", mock_provider)



@pytest.fixture
def discovery_df():
    """Generates a rich, deterministic dataset containing:

    - Strong correlation (age <-> purchase_amount)
    - Meaningful group differences (region = East has much higher purchase)
    - Cyclical time patterns (timestamps across hours)
    - Interactions
    - Data quality issues (constant column, identical column, extreme outlier, missing values)
    """
    np.random.seed(42)
    n = 60

    ages = np.linspace(20, 60, n)
    # Strong correlation with age (r ~ 0.98)
    purchases = ages * 5.0 + np.random.normal(0, 3, n)

    # Regions: East has higher spending_score (+82.9% like user example)
    regions = ["East"] * 20 + ["West"] * 20 + ["North"] * 20
    spending_score = [250.0 if r == "East" else 80.0 for r in regions]


    # Service type and time_of_day for interactions
    service_types = ["Standard", "Express"] * 30
    time_of_day = ["Morning"] * 15 + ["Evening"] * 15 + ["Morning"] * 15 + ["Evening"] * 15
    wait_time = []
    for s, t in zip(service_types, time_of_day):
        if s == "Express" and t == "Evening":
            wait_time.append(60.0)  # non-additive interaction
        elif s == "Express":
            wait_time.append(10.0)
        elif t == "Evening":
            wait_time.append(25.0)
        else:
            wait_time.append(15.0)

    # Datetime across hours (e.g. 9 AM, 12 PM, 6 PM)
    hours = [9, 12, 18] * 20
    dates = [f"2026-03-{10 + (i % 5):02d} {hours[i]:02d}:00:00" for i in range(n)]

    # Data quality items
    constant_col = ["FIXED_VALUE"] * n
    duplicate_col = list(ages)
    missing_col = [np.nan if i < 25 else 10.0 for i in range(n)]  # 41.6% missing
    outlier_col = list(purchases)
    outlier_col[0] = 50000.0  # Massive extreme outlier

    # Add a tiny group category to test filtering
    dept = ["Engineering"] * 28 + ["Sales"] * 29 + ["TinyGrp"] * 3

    return pd.DataFrame({
        "customer_age": ages,
        "purchase_amount": purchases,
        "region": regions,
        "spending_score": spending_score,
        "service_type": service_types,
        "time_of_day": time_of_day,
        "waiting_time": wait_time,
        "timestamp": dates,
        "const_feat": constant_col,
        "age_copy": duplicate_col,
        "incomplete_data": missing_col,
        "metric_with_outlier": outlier_col,
        "department": dept,
    })


# 1. Test Correlation Discovery
def test_correlation_discovery(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")
    engine = DiscoveryEngine()
    response = engine.discover(summary.dataset_id, max_findings=10)

    corr_findings = [f for f in response.findings if f.type == "correlation"]
    assert len(corr_findings) >= 1
    # Check that age <-> purchase_amount correlation is discovered
    age_purch_corr = next((f for f in corr_findings if "customer_age" in f.columns and "purchase_amount" in f.columns), None)
    assert age_purch_corr is not None
    assert age_purch_corr.metric["correlation"] > 0.7
    assert age_purch_corr.metric["direction"] == "Positive"
    assert age_purch_corr.metric["strength"] == "Strong"
    assert "sample_size" in age_purch_corr.metric
    assert "p_value" in age_purch_corr.metric
    assert "causes" not in age_purch_corr.explanation.lower()
    assert age_purch_corr.caution is not None



# 2. Test Group Difference Discovery
def test_group_difference_discovery(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")
    engine = DiscoveryEngine()
    response = engine.discover(summary.dataset_id, max_findings=15)

    grp_findings = [f for f in response.findings if f.type == "group_difference"]
    print("ACTUAL GRP FINDINGS:", [f.metric for f in grp_findings])
    assert len(grp_findings) >= 1
    # Check East group difference
    east_finding = next((f for f in grp_findings if f.metric.get("group") == "East"), None)

    assert east_finding is not None


    assert east_finding.metric["percentage_difference"] > 20.0
    assert east_finding.metric["group_size"] == 20



# 3. Test Time Pattern Discovery
def test_time_pattern_discovery(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")
    engine = DiscoveryEngine()
    response = engine.discover(summary.dataset_id, max_findings=15)

    time_findings = [f for f in response.findings if f.type == "time_pattern"]
    assert len(time_findings) >= 1
    t = time_findings[0]
    assert "temporal_unit" in t.metric
    assert "peak_segment" in t.metric
    assert "spread_percentage" in t.metric


# 4. Test Outlier & Data Quality Discovery
def test_data_quality_discovery(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")
    engine = DiscoveryEngine()
    response = engine.discover(summary.dataset_id, max_findings=15)

    dq_findings = [f for f in response.findings if f.type == "data_quality"]
    print("DQ FINDINGS IN TEST:", [(f.id, f.title, f.columns, f.metric) for f in dq_findings])
    assert len(dq_findings) >= 2


    # Check high missingness found
    null_dq = next((f for f in dq_findings if "incomplete_data" in f.columns), None)
    assert null_dq is not None
    assert null_dq.metric["missing_percentage"] > 25.0

    # Check constant column found
    const_dq = next((f for f in dq_findings if "const_feat" in f.columns), None)
    assert const_dq is not None
    assert const_dq.metric["unique_count"] == 1

    # Check duplicate columns found
    dup_dq = next((f for f in dq_findings if "age_copy" in f.columns and "customer_age" in f.columns), None)
    assert dup_dq is not None
    assert dup_dq.metric["is_exact_duplicate"] is True


# 5. Test Duplicate Correlation Removal (No A<->B and B<->A duplicate pairs)
def test_duplicate_correlation_removal(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")
    engine = DiscoveryEngine()
    response = engine.discover(summary.dataset_id, max_findings=20)

    corr_findings = [f for f in response.findings if f.type == "correlation"]
    seen_pairs = set()
    for f in corr_findings:
        pair = frozenset(f.columns)
        assert pair not in seen_pairs, f"Duplicate correlation pair found: {f.columns}"
        seen_pairs.add(pair)


# 6. Test Missing Value Handling
def test_missing_value_handling():
    # DataFrame with sporadic NaNs in both numeric and categorical columns
    df = pd.DataFrame({
        "x": [1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, np.nan, 10.0],
        "y": [2.1, np.nan, 6.2, 8.1, 10.3, 12.0, np.nan, 16.2, 18.0, 20.1],
        "cat": ["A", "A", "B", "B", np.nan, "A", "B", "A", "B", "A"],
    })
    summary = dataset_store.add_dataset(df, filename="nans.csv")
    engine = DiscoveryEngine()
    # Must not raise or return NaN metrics
    response = engine.discover(summary.dataset_id, max_findings=5)
    assert response.summary.findings_returned >= 1
    for f in response.findings:
        for k, v in f.metric.items():
            if isinstance(v, float):
                assert not np.isnan(v), f"Metric {k} was NaN in finding {f.id}"


# 7. Test Tiny Group Filtering
def test_tiny_group_filtering(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")
    engine = DiscoveryEngine()
    response = engine.discover(summary.dataset_id, max_findings=20)

    # "TinyGrp" only has 3 rows in a 60 row dataset (< 2% + small) or should be filtered if too small
    grp_findings = [f for f in response.findings if f.type == "group_difference"]
    for f in grp_findings:
        # Group size must be >= 3 and not an isolated single row
        assert f.metric.get("group_size", 0) >= 3


# 8. Test LLM Candidate-ID Validation (Reject hallucinated IDs)
def test_llm_candidate_id_validation(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")

    # Mock provider returning hallucinated candidate_id
    mock_provider = MagicMock(spec=BaseLLMProvider)
    mock_provider.provider_name = "mock_gemma"
    hallucinated_response = json.dumps({
        "selected_findings": [
            {
                "candidate_id": "INVENTED_ID_999",  # Does NOT exist
                "title": "Hallucinated Finding",
                "importance": "high",
                "explanation": "This ID was completely invented.",
            }
        ]
    })
    mock_provider.generate_text.return_value = hallucinated_response

    mock_agent = MagicMock()
    mock_agent.provider = mock_provider

    engine = DiscoveryEngine(agent_service=mock_agent)
    response = engine.discover(summary.dataset_id, max_findings=5)

    # Validated response should NOT contain the invented candidate ID
    finding_ids = [f.id for f in response.findings]
    assert "INVENTED_ID_999" not in finding_ids
    # Should cleanly fall back to deterministic findings
    assert len(response.findings) >= 1
    assert all(not f.id.startswith("INVENTED") for f in response.findings)


# 9. Test LLM Failure Fallback (Malformed JSON or Exception)
def test_llm_failure_fallback(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")

    # Case A: Provider throws exception
    mock_provider_err = MagicMock(spec=BaseLLMProvider)
    mock_provider_err.provider_name = "mock_err"
    mock_provider_err.generate_text.side_effect = RuntimeError("Rate limit or connection error")

    mock_agent_err = MagicMock()
    mock_agent_err.provider = mock_provider_err

    engine_err = DiscoveryEngine(agent_service=mock_agent_err)
    res_err = engine_err.discover(summary.dataset_id, max_findings=5)
    assert res_err.summary.findings_returned >= 1
    assert len(res_err.findings) >= 1

    # Case B: Provider returns non-JSON garbage
    mock_provider_bad = MagicMock(spec=BaseLLMProvider)
    mock_provider_bad.provider_name = "mock_bad"
    mock_provider_bad.generate_text.return_value = "Sorry, as an AI language model I cannot parse this."

    mock_agent_bad = MagicMock()
    mock_agent_bad.provider = mock_provider_bad

    engine_bad = DiscoveryEngine(agent_service=mock_agent_bad)
    res_bad = engine_bad.discover(summary.dataset_id, max_findings=5)
    assert res_bad.summary.findings_returned >= 1
    assert len(res_bad.findings) >= 1


# 10. Test Empty / Small Dataset Handling
def test_empty_and_small_dataset_handling():
    # Empty DataFrame
    empty_df = pd.DataFrame({"col_a": [], "col_b": []})
    summary_empty = dataset_store.add_dataset(empty_df, filename="empty.csv")
    engine = DiscoveryEngine()
    res_empty = engine.discover(summary_empty.dataset_id)
    assert res_empty.summary.rows == 0
    assert res_empty.summary.findings_returned == 0

    # 1-row DataFrame
    one_row_df = pd.DataFrame({"age": [25], "score": [100.0]})
    summary_one = dataset_store.add_dataset(one_row_df, filename="one.csv")
    res_one = engine.discover(summary_one.dataset_id)
    assert res_one.summary.rows == 1
    # No crashes, returns cleanly with 0 or minimal valid findings
    assert isinstance(res_one.findings, list)


# 11. Test API Endpoints
def test_discovery_api_endpoints(discovery_df):
    summary = dataset_store.add_dataset(discovery_df, filename="sales.csv")
    dataset_id = summary.dataset_id

    # POST /api/v1/discovery (body payload)
    res1 = client.post("/api/v1/discovery", json={"dataset_id": dataset_id, "max_findings": 4})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["dataset_id"] == dataset_id
    assert "summary" in data1
    assert data1["summary"]["candidates_examined"] > 0
    assert len(data1["findings"]) <= 4
    assert len(data1["findings"]) > 0

    # POST /api/v1/datasets/{dataset_id}/discovery (path param)
    res2 = client.post(f"/api/v1/datasets/{dataset_id}/discovery?max_findings=3")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["dataset_id"] == dataset_id
    assert len(data2["findings"]) <= 3

    # 404 for non-existent dataset
    res_404 = client.post("/api/v1/discovery", json={"dataset_id": "non-existent-uuid"})
    assert res_404.status_code == 404
