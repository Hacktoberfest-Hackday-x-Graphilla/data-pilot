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

def test_gemini_provider_instantiation():
    """Provider Test 1: Gemini provider can be instantiated and configured."""
    from app.services.providers import GeminiProvider
    prov = GeminiProvider(api_key="test_key", model="gemini-3-flash-preview")
    assert prov.provider_name == "gemini"
    assert prov.api_key == "test_key"
    assert prov.model_name == "gemini-3-flash-preview"

def test_gemma_provider_instantiation():
    """Provider Test 2: Gemma provider can be instantiated and configured."""
    from app.services.providers import GemmaProvider
    prov = GemmaProvider(api_key="gemma_key", model="gemma2-9b-it", base_url="https://api.groq.com/openai/v1")
    assert prov.provider_name == "gemma"
    assert prov.api_key == "gemma_key"
    assert prov.model_name == "gemma2-9b-it"
    assert prov.base_url == "https://api.groq.com/openai/v1"

def test_openai_compatible_tool_schema():
    """Provider Test 3: OpenAI-compatible tool schema is generated correctly from existing declarations."""
    from app.tools.registry import get_openai_tools, TOOL_MAP
    tools = get_openai_tools()
    assert len(tools) == len(TOOL_MAP)
    for t in tools:
        assert t["type"] == "function"
        assert "function" in t
        fn = t["function"]
        assert fn["name"] in TOOL_MAP
        assert "parameters" in fn
        assert fn["parameters"]["type"] == "object"

def test_gemma_tool_call_parsing():
    """Provider Test 4: Gemma tool call can be parsed from mock response."""
    from app.services.providers import GemmaProvider

    prov = GemmaProvider(api_key="mock", model="gemma2-9b-it")
    mock_client = MagicMock()
    prov._client = mock_client

    # Mock tool call in OpenAI format
    mock_tc = MagicMock()
    mock_tc.id = "call_abc123"
    mock_tc.function.name = "calculate_statistics"
    mock_tc.function.arguments = '{"columns": ["sales"]}'

    mock_msg = MagicMock()
    mock_msg.content = None
    mock_msg.tool_calls = [mock_tc]

    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response

    session = prov.create_chat_session(system_instruction="You are DataPilot")
    res = session.send_initial_message("What is average sales?")

    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].call_id == "call_abc123"
    assert res.tool_calls[0].name == "calculate_statistics"
    assert res.tool_calls[0].arguments == {"columns": ["sales"]}

def test_gemma_tool_result_sent_back():
    """Provider Test 5: Tool results can be sent back to the Gemma provider session."""
    from app.services.providers import GemmaProvider
    from app.services.providers.base import ToolResultItem

    prov = GemmaProvider(api_key="mock", model="gemma2-9b-it")
    mock_client = MagicMock()
    prov._client = mock_client

    mock_final_msg = MagicMock()
    mock_final_msg.content = "Average sales is 200.0."
    mock_final_msg.tool_calls = None

    mock_choice = MagicMock()
    mock_choice.message = mock_final_msg
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response

    session = prov.create_chat_session(system_instruction="You are DataPilot")
    tool_results = [
        ToolResultItem(
            call_id="call_abc123",
            name="calculate_statistics",
            result={"numeric_stats": {"sales": {"mean": 200.0}}},
            is_error=False,
        )
    ]
    res = session.send_tool_results(tool_results)

    assert res.text == "Average sales is 200.0."
    assert len(res.tool_calls) == 0
    # Verify that tool result was appended to messages history
    tool_msgs = [m for m in session.messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["tool_call_id"] == "call_abc123"
    assert "200.0" in tool_msgs[0]["content"]

def test_ai_agent_provider_selection():
    """Provider Test 6: AIAgentService selects provider based on AI_PROVIDER setting or argument."""
    # 1. Default selects gemini
    with patch("app.services.ai_agent.settings.AI_PROVIDER", "gemini"):
        agent_gemini = AIAgentService()
        assert agent_gemini.provider.provider_name == "gemini"

    # 2. Setting AI_PROVIDER to gemma selects gemma
    with patch("app.services.ai_agent.settings.AI_PROVIDER", "gemma"):
        agent_gemma = AIAgentService()
        assert agent_gemma.provider.provider_name == "gemma"

    # 3. Explicit provider_name override
    agent_explicit_gemma = AIAgentService(provider_name="gemma")
    assert agent_explicit_gemma.provider.provider_name == "gemma"

    agent_explicit_gemini = AIAgentService(provider_name="gemini")
    assert agent_explicit_gemini.provider.provider_name == "gemini"


