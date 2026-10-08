import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.dataset_store import dataset_store

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_store():
    dataset_store.clear()
    yield
    dataset_store.clear()

def test_root_and_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "gemini_model" in data
    assert "gemini_key_configured" in data
    # Ensure raw API key is NEVER exposed
    assert "GEMINI_API_KEY" not in str(data)

def test_get_tools_endpoint():
    res = client.get("/api/v1/tools")
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    assert len(data["tools"]) == 6
    assert "gemini_function_declarations" in data
    assert len(data["gemini_function_declarations"]) == 6

def test_upload_and_profile_flow():
    csv_content = b"region,sales,leads\nNorth,500,20\nSouth,300,15\nEast,700,35\nWest,450,22\n"
    
    # 1. Upload
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("quarterly_sales.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert upload_res.status_code == 201
    summary = upload_res.json()
    dataset_id = summary["dataset_id"]
    assert summary["row_count"] == 4
    assert summary["column_count"] == 3
    assert "sales" in summary["columns"]

    # 2. Get Profile
    profile_res = client.post(f"/api/v1/datasets/{dataset_id}/profile")
    assert profile_res.status_code == 200
    profile = profile_res.json()
    assert profile["row_count"] == 4
    assert profile["column_count"] == 3
    assert len(profile["columns"]) == 3
    assert "sales" in profile["numeric_columns"]

    # 3. Execute tool via API
    tool_res = client.post(
        f"/api/v1/datasets/{dataset_id}/tools/execute",
        json={
            "tool_name": "calculate_statistics",
            "parameters": {"columns": ["sales"]},
        },
    )
    assert tool_res.status_code == 200
    tool_data = tool_res.json()
    assert tool_data["success"] is True
    assert tool_data["data"]["numeric_stats"]["sales"]["mean"] == 487.5

def test_upload_empty_csv():
    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

def test_upload_non_csv():
    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("data.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    assert res.status_code == 400
    assert "only .csv" in res.json()["detail"].lower()
