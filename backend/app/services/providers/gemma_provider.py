import json
from typing import Any, Optional
from openai import OpenAI

from app.config import settings
from app.tools.registry import get_openai_tools
from .base import BaseChatSession, BaseLLMProvider, ProviderResponse, ToolCallItem, ToolResultItem

class GemmaChatSession(BaseChatSession):
    """Wraps OpenAI-compatible chat completion sessions (Gemma runtime) to adhere to BaseChatSession."""

    def __init__(self, client: OpenAI, model_name: str, system_instruction: str):
        self.client = client
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_instruction}
        ]
        self.tools = get_openai_tools()

    def send_initial_message(self, prompt: str) -> ProviderResponse:
        self.messages.append({"role": "user", "content": prompt})
        return self._call_model(tools=self.tools)

    def send_tool_results(self, results: list[ToolResultItem]) -> ProviderResponse:
        for r in results:
            content_str = json.dumps({"error": str(r.result)} if r.is_error else r.result, default=str)
            self.messages.append({
                "role": "tool",
                "tool_call_id": r.call_id,
                "name": r.name,
                "content": content_str,
            })
        return self._call_model(tools=self.tools)

    def send_synthesis_prompt(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        try:
            res = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                temperature=0.2,
            )
            msg = res.choices[0].message
            return getattr(msg, "content", "") or ""
        except Exception:
            return "Maximum analysis iterations reached. The gathered tool evidence has been recorded in the trace."

    def _call_model(self, tools: Optional[list[dict[str, Any]]] = None) -> ProviderResponse:
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": self.messages,
            "temperature": 0.2,
        }
        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        # Append assistant message to ongoing message history
        assistant_dict: dict[str, Any] = {"role": "assistant"}
        if getattr(msg, "content", None):
            assistant_dict["content"] = msg.content
        if getattr(msg, "tool_calls", None):
            assistant_dict["tool_calls"] = msg.tool_calls
        self.messages.append(assistant_dict)

        # Parse tool calls
        parsed_tool_calls: list[ToolCallItem] = []
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for idx, tc in enumerate(tool_calls):
                call_id = getattr(tc, "id", "") or f"call_{idx}"
                func = getattr(tc, "function", None)
                if func:
                    func_name = getattr(func, "name", "")
                    raw_args = getattr(func, "arguments", "{}")
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except Exception:
                            args = {}
                    elif isinstance(raw_args, dict):
                        args = raw_args
                    else:
                        args = {}
                    parsed_tool_calls.append(ToolCallItem(call_id=call_id, name=func_name, arguments=args))

        text = getattr(msg, "content", None) or None
        return ProviderResponse(text=text, tool_calls=parsed_tool_calls)

class GemmaProvider(BaseLLMProvider):
    """OpenAI-compatible Gemma provider backend (Groq, Ollama, Together, vLLM)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMMA_API_KEY
        self.model_name = model or settings.GEMMA_MODEL
        self.base_url = base_url or settings.GEMMA_API_BASE
        self._client: Optional[OpenAI] = None

    @property
    def provider_name(self) -> str:
        return "gemma"

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            # For local Ollama or endpoints without auth, fall back to placeholder key
            key = self.api_key.strip() if (self.api_key and self.api_key.strip()) else "dummy-api-key"
            self._client = OpenAI(
                api_key=key,
                base_url=self.base_url if self.base_url else None,
            )
        return self._client

    def create_chat_session(self, system_instruction: str) -> GemmaChatSession:
        return GemmaChatSession(
            client=self.client,
            model_name=self.model_name,
            system_instruction=system_instruction,
        )

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            res = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
            msg = res.choices[0].message
            return getattr(msg, "content", "") or ""
        except Exception:
            return ""
