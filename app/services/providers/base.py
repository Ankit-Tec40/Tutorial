from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional
from pydantic import BaseModel, Field


class ConnectionTestResult(BaseModel):
    success: bool
    provider: str
    message: str
    available_models: List[str] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    error_code: Optional[str] = None
    setup_instructions: Optional[str] = None


class ProviderResponse(BaseModel):
    content: str
    model: str
    provider: str
    latency_ms: float = 0.0
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers (Gemini, Ollama, etc.)."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the canonical provider name (e.g. 'gemini', 'ollama')."""
        pass

    @abstractmethod
    def test_connection(self) -> ConnectionTestResult:
        """Tests connectivity and configuration for this provider."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """Lists available models for this provider."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ProviderResponse:
        """Generates a synchronous response."""
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Streams text chunks for chat."""
        pass
