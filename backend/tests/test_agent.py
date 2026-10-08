from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.dataset_store import dataset_store
from app.services.ai_agent import AIAgentService

client = TestClient(app)

class MockFunctionCall:
    def __init__(self, name: str, args: dict):
        self.name = name
        self.args = args

class MockResponse:
    def __init__(self, text: str = None, function_calls: list = None):
        self.text = text
        self.function_calls = function_calls or []

@pytest.fixture
def dataset_id():
    """Populates store with a test dataset."""
    df = pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "sales": [100.0, 250.0, 300.0, 150.0],
        "units": [10, 25, 30, 15],
    })
    summary = dataset_store.add_dataset(df, "sales_data.csv")
    yield summary.dataset_id
    dataset_store.clear()

def test_chat_validation_empty_question(dataset_id):
    """Test 1: Chat endpoint validation on empty question."""
    res = client.post(f"/api/v1/datasets/{dataset_id}/chat", json={"question": ""})
    assert res.status_code == 422

def test_chat_invalid_dataset_id():
    """Test 2: Chat endpoint returns 404 for non-existent dataset."""
    res = client.post("/api/v1/datasets/invalid-id-999/chat", json={"question": "What is the total sales?"})
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_chat_missing_api_key(dataset_id):
    """Test 3: Missing API key returns a clean, descriptive 400 error."""
    agent_no_key = AIAgentService(api_key="")
    with patch("app.api.v1.analysis.ai_agent", agent_no_key):
        res = client.post(f"/api/v1/datasets/{dataset_id}/chat", json={"question": "Summarize data"})
        assert res.status_code == 400
        assert "gemini_api_key is not configured" in res.json()["detail"].lower()

def test_mocked_ai_single_tool_loop(dataset_id):
    """Test 4 & 5: Mocked single tool call loop and execution."""
    mock_chat = MagicMock()
    # Turn 1: model asks to calculate_statistics
    turn1_res = MockResponse(
        text=None,
        function_calls=[MockFunctionCall("calculate_statistics", {"columns": ["sales"]})]
    )
    # Turn 2: model provides final answer
    turn2_res = MockResponse(
        text="The average sales across all regions is 200.0 with maximum sales of 300.0 in the East.",
        function_calls=[]
    )
    mock_chat.send_message.side_effect = [turn1_res, turn2_res]

    agent = AIAgentService(api_key="mock_key")
    agent._client = MagicMock()
    agent._client.chats.create.return_value = mock_chat

    with patch("app.api.v1.analysis.ai_agent", agent):
        res = client.post(f"/api/v1/datasets/{dataset_id}/chat", json={"question": "What is the average sales?"})
        assert res.status_code == 200
        data = res.json()
        assert data["dataset_id"] == dataset_id
        assert "200.0" in data["answer"]
        assert len(data["tool_trace"]) == 1
        assert data["tool_trace"][0]["tool_name"] == "calculate_statistics"
        assert data["tool_trace"][0]["success"] is True

def test_mocked_ai_multi_step_tool_loop(dataset_id):
    """Test 6: Multi-step tool calls (e.g., group_and_compare followed by create_chart)."""
    mock_chat = MagicMock()
    # Turn 1: group_and_compare
    turn1 = MockResponse(
        function_calls=[MockFunctionCall("group_and_compare", {
            "group_by": "region",
            "metric_columns": ["sales"],
            "aggregations": ["mean"]
        })]
    )
    # Turn 2: create_chart
    turn2 = MockResponse(
        function_calls=[MockFunctionCall("create_chart", {
            "chart_type": "bar",
            "x": "region",
            "y": "sales"
        })]
    )
    # Turn 3: final answer
    turn3 = MockResponse(
        text="Sales are highest in East (300) and lowest in North (100). A bar chart has been generated.",
        function_calls=[]
    )
    mock_chat.send_message.side_effect = [turn1, turn2, turn3]

    agent = AIAgentService(api_key="mock_key")
    agent._client = MagicMock()
    agent._client.chats.create.return_value = mock_chat

    with patch("app.api.v1.analysis.ai_agent", agent):
        res = client.post(f"/api/v1/datasets/{dataset_id}/chat", json={"question": "Compare regional sales with a chart"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["tool_trace"]) == 2
        assert data["tool_trace"][0]["tool_name"] == "group_and_compare"
        assert data["tool_trace"][1]["tool_name"] == "create_chart"
        assert len(data["suggested_charts"]) == 1
        assert data["suggested_charts"][0]["chart_type"] == "bar"

def test_max_tool_call_protection(dataset_id):
    """Test 7: Loop safely stops when hitting max_tool_iterations."""
    mock_chat = MagicMock()
    # Model keeps repeatedly calling a tool
    continuous_call = MockResponse(
        function_calls=[MockFunctionCall("calculate_statistics", {"columns": ["sales"]})]
    )
    synthesis_reply = MockResponse(
        text="Max tool iterations reached. Synthesized answer based on gathered evidence.",
        function_calls=[]
    )
    # 3 loop iterations + 1 synthesis call
    mock_chat.send_message.side_effect = [continuous_call, continuous_call, continuous_call, synthesis_reply]

    agent = AIAgentService(api_key="mock_key")
    agent._client = MagicMock()
    agent._client.chats.create.return_value = mock_chat

    # Call with max_tool_iterations = 3
    response = agent.chat(dataset_id=dataset_id, question="Deep loop", max_tool_iterations=3)
    assert len(response.tool_trace) == 3
    assert "Synthesized answer" in response.answer

def test_investigate_endpoint(dataset_id):
    """Test 8: Investigation endpoint runs tool analyses and synthesizes findings."""
    res = client.post(f"/api/v1/datasets/{dataset_id}/investigate")
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_id"] == dataset_id
    assert "findings" in data
    assert len(data["tool_trace"]) >= 3
    # Check that profiling, stats, and comparisons were run
    tool_names = [t["tool_name"] for t in data["tool_trace"]]
    assert "profile_dataset" in tool_names
    assert "calculate_statistics" in tool_names

def test_tool_dispatch_with_parameter_variations(dataset_id):
    """Test 9: Tool execution normalizes LLM parameter aliases gracefully."""
    from app.tools.registry import execute_tool
    df = dataset_store.get_dataset(dataset_id)

    # 1. group_and_compare with "metrics" and "aggregation" (aliases)
    res_comp = execute_tool(df, "group_and_compare", {
        "group_by": "region",
        "metrics": ["sales"],
        "aggregation": "mean"
    })
    assert "results" in res_comp
    assert res_comp["group_by"] == "region"
    assert "sales" in res_comp["metrics_evaluated"]

    # 2. calculate_statistics with singular "column" as string
    res_stats = execute_tool(df, "calculate_statistics", {"column": "sales"})
    assert "sales" in res_stats["numeric_stats"]

    # 3. create_chart with "x_axis" and "y_axis" aliases
    res_chart = execute_tool(df, "create_chart", {
        "chart_type": "bar",
        "x_axis": "region",
        "y_axis": "sales"
    })
    assert res_chart["chart_type"] == "bar"
    assert res_chart["x_axis"] == "region"
    assert len(res_chart["data"]) == 4

def test_agent_security_blocks_unauthorized_tools(dataset_id):
    """Test 10: Model attempting unauthorized functions is strictly blocked."""
    mock_chat = MagicMock()
    # Turn 1: model attempts unauthorized tool call
    turn1 = MockResponse(
        function_calls=[MockFunctionCall("run_shell_command", {"command": "ls -la"})]
    )
    # Turn 2: model recovers and provides text response
    turn2 = MockResponse(
        text="I cannot run shell commands, but I can analyze your dataset using approved tools.",
        function_calls=[]
    )
    mock_chat.send_message.side_effect = [turn1, turn2]

    agent = AIAgentService(api_key="mock_key")
    agent._client = MagicMock()
    agent._client.chats.create.return_value = mock_chat

    with patch("app.api.v1.analysis.ai_agent", agent):
        res = client.post(f"/api/v1/datasets/{dataset_id}/chat", json={"question": "Run shell"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["tool_trace"]) == 1
        assert data["tool_trace"][0]["tool_name"] == "run_shell_command"
        assert data["tool_trace"][0]["success"] is False
        assert "Security Error" in data["tool_trace"][0]["summary"]

def test_tool_execution_error_handled_gracefully(dataset_id):
    """Test 11: Tool execution failure is recorded in trace and handled without crashing."""
    mock_chat = MagicMock()
    # Turn 1: model requests group_and_compare with non-existent column
    turn1 = MockResponse(
        function_calls=[MockFunctionCall("group_and_compare", {
            "group_by": "missing_column",
            "metric_columns": ["sales"]
        })]
    )
    # Turn 2: model acknowledges error
    turn2 = MockResponse(
        text="The requested column 'missing_column' was not found in the dataset.",
        function_calls=[]
    )
    mock_chat.send_message.side_effect = [turn1, turn2]

    agent = AIAgentService(api_key="mock_key")
    agent._client = MagicMock()
    agent._client.chats.create.return_value = mock_chat

    with patch("app.api.v1.analysis.ai_agent", agent):
        res = client.post(f"/api/v1/datasets/{dataset_id}/chat", json={"question": "Group by missing"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["tool_trace"]) == 1
        assert data["tool_trace"][0]["success"] is False
        assert "Execution error in group_and_compare" in data["tool_trace"][0]["summary"]

