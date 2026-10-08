from typing import Any, Optional
from google import genai
from google.genai import types

from app.config import settings
from app.tools.registry import get_genai_tools
from .base import BaseChatSession, BaseLLMProvider, ProviderResponse, ToolCallItem, ToolResultItem

class GeminiChatSession(BaseChatSession):
    """Wraps Google GenAI Chat session to adhere to BaseChatSession."""

    def __init__(self, chat_session: Any):
        self._chat = chat_session

    def send_initial_message(self, prompt: str) -> ProviderResponse:
        response = self._chat.send_message(prompt)
        return self._parse_response(response)

    def send_tool_results(self, results: list[ToolResultItem]) -> ProviderResponse:
        parts = []
        for r in results:
            content = {"error": str(r.result)} if r.is_error else {"result": r.result}
            part = types.Part.from_function_response(name=r.name, response=content)
            parts.append(part)
        response = self._chat.send_message(parts)
        return self._parse_response(response)

    def send_synthesis_prompt(self, prompt: str) -> str:
        try:
            res = self._chat.send_message(prompt)
            return getattr(res, "text", "") or ""
        except Exception:
            return "Maximum analysis iterations reached. The gathered tool evidence has been recorded in the trace."

    def _parse_response(self, response: Any) -> ProviderResponse:
        tool_calls: list[ToolCallItem] = []
        function_calls = getattr(response, "function_calls", None)
        if function_calls:
            for idx, fc in enumerate(function_calls):
                call_id = getattr(fc, "id", "") or f"call_{idx}_{fc.name}"
                args = dict(fc.args) if getattr(fc, "args", None) else {}
                tool_calls.append(ToolCallItem(call_id=call_id, name=fc.name, arguments=args))
        text = getattr(response, "text", None) or None
        return ProviderResponse(text=text, tool_calls=tool_calls)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider backend using official Google GenAI Python SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self._client: Optional[genai.Client] = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key or not self.api_key.strip():
                raise ValueError("GEMINI_API_KEY is not configured in environment.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def create_chat_session(self, system_instruction: str) -> GeminiChatSession:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=get_genai_tools(),
            temperature=0.2,
        )
        chat = self.client.chats.create(model=self.model_name, config=config)
        return GeminiChatSession(chat)

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.api_key or not self.api_key.strip():
            return ""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        ) if system_instruction else None
        res = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return getattr(res, "text", "") or ""
