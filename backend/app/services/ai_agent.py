import json
from typing import Any, Optional
import pandas as pd
from google import genai
from google.genai import types

from app.config import settings
from app.models.schemas import (
    ChatResponse,
    InvestigateResponse,
    InvestigationFinding,
    ToolTraceItem,
)
from app.services.dataset_store import dataset_store
from app.tools.registry import (
    TOOL_MAP,
    execute_tool,
    get_genai_tools,
    summarize_tool_result,
)
from app.tools.profiling import profile_dataset
from app.tools.statistics import calculate_statistics
from app.tools.anomalies import detect_anomalies
from app.tools.correlations import find_correlations
from app.tools.comparisons import group_and_compare
from app.tools.charts import create_chart

MAX_TOOL_CALLS = 8

SYSTEM_INSTRUCTION = """You are DataPilot, an expert AI data analyst.

Your mission is to analyze the user's dataset and answer their analytical questions with factual, mathematical precision.

STRICT OPERATIONAL RULES:
1. Never invent or hallucinate statistics, metrics, correlations, anomalies, or numbers.
2. The provided Python/Pandas tools are your SINGLE SOURCE OF TRUTH for all numerical calculations.
3. Whenever numerical evidence is needed to answer a question or substantiate a claim, invoke the appropriate registered tool.
4. You may call multiple tools step-by-step for complex questions (e.g. first inspect columns/groups, then calculate statistics or correlations, then create charts).
5. Once you have collected sufficient evidence from tools, provide a structured, concise, natural-language explanation citing the specific computed figures.
6. If the dataset does not contain sufficient columns or data rows to answer the question, state that clearly instead of guessing.
7. Use the `create_chart` tool when visualization adds clarity to your findings.
"""

class AIAgentService:
    """Orchestrates DataPilot's AI Analyst Agent loop with Python/Pandas tool execution."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key or not self.api_key.strip():
                raise ValueError("GEMINI_API_KEY is not configured in environment.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _build_dataset_context(self, df: pd.DataFrame, filename: str) -> str:
        """Constructs concise dataset metadata for model prompt without leaking excessive raw data."""
        row_count = len(df)
        col_count = len(df.columns)
        
        col_info = []
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            null_cnt = int(df[col].isna().sum())
            col_info.append(f"  - {col} ({dtype_str}, {null_cnt} missing)")

        head_records = df.head(3).to_dict(orient="records")
        # Sanitize any NaN for json serialization in prompt
        head_sample = json.dumps(head_records, default=str)

        return (
            f"DATASET CONTEXT:\n"
            f"- Filename: {filename}\n"
            f"- Dimensions: {row_count} rows, {col_count} columns\n"
            f"- Columns & Types:\n" + "\n".join(col_info) + "\n"
            f"- Sample Data (first 3 rows):\n{head_sample}\n"
        )

    def chat(
        self,
        dataset_id: str,
        question: str,
        max_tool_iterations: int = MAX_TOOL_CALLS
    ) -> ChatResponse:
        """Executes the AI analyst loop for a specific user question."""
        df = dataset_store.get_dataset(dataset_id)
        if df is None:
            raise KeyError(f"Dataset with ID '{dataset_id}' not found.")

        if not self.api_key or not self.api_key.strip():
            raise ValueError("GEMINI_API_KEY is not configured in environment.")

        meta = dataset_store.get_metadata(dataset_id) or {}
        filename = meta.get("filename", "dataset.csv")

        dataset_context = self._build_dataset_context(df, filename)
        user_prompt = f"{dataset_context}\n\nUSER QUESTION: {question}\n\nInvestigate using the appropriate analysis tools and answer with evidence."

        tool_trace: list[ToolTraceItem] = []
        suggested_charts: list[dict[str, Any]] = []

        # Configure GenAI client session
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=get_genai_tools(),
            temperature=0.2,
        )

        chat_session = self.client.chats.create(
            model=self.model_name,
            config=config,
        )

        current_message: Any = user_prompt
        final_answer = ""

        for iteration in range(max_tool_iterations):
            response = chat_session.send_message(current_message)

            # Check if model requested function calls
            function_calls = response.function_calls

            if not function_calls:
                # No more function calls; model has provided its final text response
                final_answer = response.text or ""
                break

            # Process function calls
            function_response_parts = []
            for call in function_calls:
                tool_name = call.name
                call_args = dict(call.args) if call.args else {}

                # Strict security: ONLY execute registered tools from TOOL_MAP
                if tool_name not in TOOL_MAP:
                    err_msg = f"Security Error: Tool '{tool_name}' is not in the approved tool registry."
                    tool_trace.append(
                        ToolTraceItem(
                            tool_name=tool_name,
                            parameters=call_args,
                            success=False,
                            summary=err_msg,
                        )
                    )
                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"error": err_msg},
                        )
                    )
                    continue

                try:
                    tool_output = execute_tool(df, tool_name, call_args)
                    summary = summarize_tool_result(tool_name, tool_output)

                    if tool_name == "create_chart" and isinstance(tool_output, dict):
                        suggested_charts.append(tool_output)

                    tool_trace.append(
                        ToolTraceItem(
                            tool_name=tool_name,
                            parameters=call_args,
                            success=True,
                            summary=summary,
                            data=tool_output,
                        )
                    )
                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": tool_output},
                        )
                    )
                except Exception as ex:
                    err_str = f"Execution error in {tool_name}: {str(ex)}"
                    tool_trace.append(
                        ToolTraceItem(
                            tool_name=tool_name,
                            parameters=call_args,
                            success=False,
                            summary=err_str,
                        )
                    )
                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"error": err_str},
                        )
                    )

            current_message = function_response_parts
        else:
            # Exceeded max_tool_iterations without a final text response
            synthesis_prompt = "You have reached the maximum number of tool executions. Please summarize your findings and provide your final answer based on the computed evidence gathered so far."
            final_res = chat_session.send_message(synthesis_prompt)
            final_answer = final_res.text or "Analysis completed with available tool evidence."

        return ChatResponse(
            dataset_id=dataset_id,
            question=question,
            answer=final_answer.strip(),
            tool_trace=tool_trace,
            suggested_charts=suggested_charts,
        )

    def investigate(self, dataset_id: str) -> InvestigateResponse:
        """Executes systematic multi-tool dataset investigation and synthesizes ranked findings."""
        df = dataset_store.get_dataset(dataset_id)
        if df is None:
            raise KeyError(f"Dataset with ID '{dataset_id}' not found.")

        meta = dataset_store.get_metadata(dataset_id) or {}
        filename = meta.get("filename", "dataset.csv")

        tool_trace: list[ToolTraceItem] = []
        collected_evidence: dict[str, Any] = {}
        charts: list[dict[str, Any]] = []

        # 1. Profile dataset
        try:
            profile = profile_dataset(df)
            collected_evidence["profile"] = profile
            tool_trace.append(ToolTraceItem(
                tool_name="profile_dataset",
                parameters={},
                success=True,
                summary=summarize_tool_result("profile_dataset", profile),
                data=profile,
            ))
        except Exception as e:
            collected_evidence["profile"] = {"error": str(e)}

        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])]
        categorical_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]

        # 2. Key statistics
        try:
            stats = calculate_statistics(df)
            collected_evidence["statistics"] = stats
            tool_trace.append(ToolTraceItem(
                tool_name="calculate_statistics",
                parameters={"columns": list(df.columns)},
                success=True,
                summary=summarize_tool_result("calculate_statistics", stats),
                data=stats,
            ))
        except Exception as e:
            collected_evidence["statistics"] = {"error": str(e)}

        # 3. Detect anomalies
        if numeric_cols:
            try:
                anomalies = detect_anomalies(df, columns=numeric_cols, method="iqr")
                collected_evidence["anomalies"] = anomalies
                tool_trace.append(ToolTraceItem(
                    tool_name="detect_anomalies",
                    parameters={"columns": numeric_cols, "method": "iqr"},
                    success=True,
                    summary=summarize_tool_result("detect_anomalies", anomalies),
                    data=anomalies,
                ))
            except Exception as e:
                collected_evidence["anomalies"] = {"error": str(e)}

        # 4. Correlations
        if len(numeric_cols) >= 2:
            try:
                corrs = find_correlations(df, columns=numeric_cols)
                collected_evidence["correlations"] = corrs
                tool_trace.append(ToolTraceItem(
                    tool_name="find_correlations",
                    parameters={"columns": numeric_cols},
                    success=True,
                    summary=summarize_tool_result("find_correlations", corrs),
                    data=corrs,
                ))
            except Exception as e:
                collected_evidence["correlations"] = {"error": str(e)}

        # 5. Group comparisons
        if categorical_cols and numeric_cols:
            best_cat = categorical_cols[0]
            best_num = numeric_cols[:2]
            try:
                comp = group_and_compare(df, group_by=best_cat, metric_columns=best_num)
                collected_evidence["group_comparison"] = comp
                tool_trace.append(ToolTraceItem(
                    tool_name="group_and_compare",
                    parameters={"group_by": best_cat, "metric_columns": best_num},
                    success=True,
                    summary=summarize_tool_result("group_and_compare", comp),
                    data=comp,
                ))
            except Exception as e:
                collected_evidence["group_comparison"] = {"error": str(e)}

        # 6. Chart creation
        if categorical_cols and numeric_cols:
            try:
                chart_spec = create_chart(df, chart_type="bar", x=categorical_cols[0], y=numeric_cols[0], aggregation="mean")
                charts.append(chart_spec)
                tool_trace.append(ToolTraceItem(
                    tool_name="create_chart",
                    parameters={"chart_type": "bar", "x": categorical_cols[0], "y": numeric_cols[0]},
                    success=True,
                    summary=summarize_tool_result("create_chart", chart_spec),
                    data=chart_spec,
                ))
            except Exception as e:
                pass
        elif len(numeric_cols) >= 2:
            try:
                chart_spec = create_chart(df, chart_type="scatter", x=numeric_cols[0], y=numeric_cols[1])
                charts.append(chart_spec)
                tool_trace.append(ToolTraceItem(
                    tool_name="create_chart",
                    parameters={"chart_type": "scatter", "x": numeric_cols[0], "y": numeric_cols[1]},
                    success=True,
                    summary=summarize_tool_result("create_chart", chart_spec),
                    data=chart_spec,
                ))
            except Exception as e:
                pass

        # Synthesize findings using Gemini (with deterministic rule-based fallback if offline)
        findings, summary_text = self._synthesize_investigation(filename, collected_evidence)

        return InvestigateResponse(
            dataset_id=dataset_id,
            summary=summary_text,
            findings=findings,
            tool_trace=tool_trace,
            charts=charts,
        )

    def _synthesize_investigation(
        self,
        filename: str,
        evidence: dict[str, Any]
    ) -> tuple[list[InvestigationFinding], str]:
        """Synthesizes structured findings from tool calculations using Gemini, with deterministic fallback."""
        findings: list[InvestigationFinding] = []

        # Deterministic extraction of core observations
        anom_data = evidence.get("anomalies", {}).get("anomalies", {})
        for col, info in anom_data.items():
            if isinstance(info, dict) and info.get("outlier_count", 0) > 0:
                findings.append(InvestigationFinding(
                    category="anomaly",
                    title=f"Statistical Outliers in '{col}'",
                    description=f"Detected {info['outlier_count']} outlier values ({info.get('outlier_percentage', 0)}% of dataset) outside normal IQR boundaries.",
                    importance="high" if info["outlier_count"] > 2 else "medium",
                    evidence=info,
                ))

        corr_pairs = evidence.get("correlations", {}).get("top_correlated_pairs", [])
        if corr_pairs:
            top_p = corr_pairs[0]
            corr_val = top_p.get("correlation", 0)
            rel_type = "positive" if corr_val > 0 else "negative"
            findings.append(InvestigationFinding(
                category="correlation",
                title=f"Strong {rel_type.capitalize()} Correlation: {top_p.get('feature_1')} vs {top_p.get('feature_2')}",
                description=f"A strong {rel_type} relationship (r = {corr_val}) was detected between {top_p.get('feature_1')} and {top_p.get('feature_2')}.",
                importance="high" if abs(corr_val) > 0.7 else "medium",
                evidence=top_p,
            ))

        grp = evidence.get("group_comparison", {})
        if grp and "results" in grp:
            findings.append(InvestigationFinding(
                category="comparison",
                title=f"Group Variations by '{grp.get('group_by')}'",
                description=f"Clear variance observed across {grp.get('total_groups', 0)} distinct groups for metrics: {', '.join(grp.get('metrics_evaluated', []))}.",
                importance="medium",
                evidence={"group_by": grp.get("group_by"), "total_groups": grp.get("total_groups")},
            ))

        # Basic summary
        profile = evidence.get("profile", {})
        row_cnt = profile.get("row_count", 0)
        col_cnt = profile.get("column_count", 0)
        summary_text = f"Dataset '{filename}' analyzed ({row_cnt} records, {col_cnt} columns). Identified {len(findings)} key findings across anomalies, correlations, and feature distributions."

        # Attempt to enrich with Gemini if client is active
        try:
            if settings.has_gemini_key:
                enrich_prompt = (
                    f"Dataset: {filename} ({row_cnt} rows, {col_cnt} columns).\n"
                    f"Computed Evidence:\n{json.dumps(evidence, default=str)[:3000]}\n\n"
                    f"Task: Provide a 2-sentence executive summary of the most important takeaways from this evidence."
                )
                res = self.client.models.generate_content(
                    model=self.model_name,
                    contents=enrich_prompt,
                )
                if res.text and len(res.text.strip()) > 0:
                    summary_text = res.text.strip()
        except Exception:
            # Fall back cleanly to deterministic summary
            pass

        return findings, summary_text

ai_agent = AIAgentService()
