from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class ToolCallItem:
    call_id: str
    name: str
    arguments: dict[str, Any]

@dataclass
class ProviderResponse:
    text: Optional[str] = None
    tool_calls: list[ToolCallItem] = field(default_factory=list)

@dataclass
class ToolResultItem:
    call_id: str
    name: str
    result: Any
    is_error: bool = False

class BaseChatSession(ABC):
    """Abstract interface for a multi-turn chat session with tool execution."""

    @abstractmethod
    def send_initial_message(self, prompt: str) -> ProviderResponse:
        """Sends the initial user prompt (with dataset context) to the model."""
        pass

    @abstractmethod
    def send_tool_results(self, results: list[ToolResultItem]) -> ProviderResponse:
        """Sends tool execution outputs back to the model."""
        pass

    @abstractmethod
    def send_synthesis_prompt(self, prompt: str) -> str:
        """Sends a final synthesis prompt when max iterations are reached."""
        pass

class BaseLLMProvider(ABC):
    """Abstract interface for LLM provider backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'gemini', 'gemma')."""
        pass

    @abstractmethod
    def create_chat_session(self, system_instruction: str) -> BaseChatSession:
        """Initializes a new multi-turn chat session with tools attached."""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generates a one-off text completion (e.g. for investigation summaries)."""
        pass
