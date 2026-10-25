import os
import time
import logging
from typing import List, Dict, Any, Generator, Optional
from app.services.providers.base import BaseLLMProvider, ProviderResponse, ConnectionTestResult

logger = logging.getLogger(__name__)

SUPPORTED_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation using the official google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        selected_model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        super().__init__(model_name=selected_model)
        self._client = None

    @property
    def name(self) -> str:
        return "gemini"

    def _get_client(self):
        """Lazy initialization of google-genai Client."""
        if not self.api_key:
            raise ValueError(
                "Gemini API Key is not configured. Add your GEMINI_API_KEY to your .env file."
            )
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def test_connection(self) -> ConnectionTestResult:
        """Tests connectivity and credentials with Google Gemini."""
        if not self.api_key:
            return ConnectionTestResult(
                success=False,
                provider="gemini",
                message="GEMINI_API_KEY is not configured.",
                available_models=SUPPORTED_GEMINI_MODELS,
                error_code="MISSING_API_KEY",
                setup_instructions="Obtain an API key from Google AI Studio (https://aistudio.google.com/) and add GEMINI_API_KEY=your_key to your .env file.",
            )

        start_time = time.perf_counter()
        try:
            client = self._get_client()
            # Run a lightweight probe to verify credentials and quota
            from google.genai import types
            response = client.models.generate_content(
                model=self.model_name or "gemini-2.5-flash",
                contents="Ping",
                config=types.GenerateContentConfig(
                    max_output_tokens=5,
                    temperature=0.0,
                ),
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # Fetch discovered models if possible
            models = self.list_models()

            return ConnectionTestResult(
                success=True,
                provider="gemini",
                message=f"Connected successfully to Gemini ({self.model_name}).",
                available_models=models,
                latency_ms=round(elapsed_ms, 2),
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_str = str(e)
            error_code = "CONNECTION_ERROR"
            setup_hint = None

            if "API_KEY_INVALID" in error_str or "invalid API key" in error_str.lower():
                error_code = "INVALID_API_KEY"
                setup_hint = "The provided GEMINI_API_KEY was rejected by Google AI Studio. Please verify the key."
            elif "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower() or "429" in error_str:
                error_code = "QUOTA_EXCEEDED"
                setup_hint = "Gemini API rate limit or quota exceeded. Consider waiting a moment or using local Ollama."

            logger.error("Gemini connection test failed: %s", error_str)
            return ConnectionTestResult(
                success=False,
                provider="gemini",
                message=f"Gemini connection test failed: {error_str}",
                available_models=SUPPORTED_GEMINI_MODELS,
                latency_ms=round(elapsed_ms, 2),
                error_code=error_code,
                setup_instructions=setup_hint,
            )

    def list_models(self) -> List[str]:
        """Returns available Gemini models."""
        try:
            if self.api_key:
                client = self._get_client()
                discovered = []
                for m in client.models.list():
                    name = getattr(m, "name", "")
                    if "gemini" in name.lower():
                        clean_name = name.replace("models/", "")
                        discovered.append(clean_name)
                if discovered:
                    return sorted(list(set(discovered)))
        except Exception as e:
            logger.debug("Could not list remote Gemini models, falling back to static list: %s", e)
        return SUPPORTED_GEMINI_MODELS

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ProviderResponse:
        """Generates a response using Gemini."""
        client = self._get_client()
        from google.genai import types

        config_kwargs: Dict[str, Any] = {
            "temperature": float(temperature),
        }
        if max_tokens:
            config_kwargs["max_output_tokens"] = int(max_tokens)
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        # Tool calling configuration if provided
        if tools:
            # Pass tool declarations into GenerateContentConfig
            config_kwargs["tools"] = tools

        start_time = time.perf_counter()
        try:
            config = types.GenerateContentConfig(**config_kwargs)
            model_to_use = self.model_name or "gemini-2.5-flash"
            response = client.models.generate_content(
                model=model_to_use,
                contents=prompt,
                config=config,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # Extract token metadata if available
            p_tokens, c_tokens, t_tokens = None, None, None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                p_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
                c_tokens = getattr(response.usage_metadata, "candidates_token_count", None)
                t_tokens = getattr(response.usage_metadata, "total_token_count", None)

            # Check for function/tool calls in candidates
            extracted_tool_calls = []
            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            extracted_tool_calls.append({
                                "name": getattr(fc, "name", ""),
                                "args": getattr(fc, "args", {}),
                            })

            content_text = response.text or ""

            return ProviderResponse(
                content=content_text,
                model=model_to_use,
                provider="gemini",
                latency_ms=round(elapsed_ms, 2),
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
                tool_calls=extracted_tool_calls if extracted_tool_calls else None,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("Gemini generate call failed: %s", e)
            raise RuntimeError(f"Gemini API Error: {str(e)}")

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Streams conversation response from Gemini."""
        client = self._get_client()
        from google.genai import types

        config_kwargs: Dict[str, Any] = {
            "temperature": float(temperature),
        }
        if max_tokens:
            config_kwargs["max_output_tokens"] = int(max_tokens)
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        config = types.GenerateContentConfig(**config_kwargs)

        # Build conversation contents
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # Gemini expects 'user' or 'model'
            api_role = "model" if role in ("assistant", "model") else "user"
            contents.append(types.Content(
                role=api_role,
                parts=[types.Part.from_text(text=content)]
            ))

        model_to_use = self.model_name or "gemini-2.5-flash"
        for chunk in client.models.generate_content_stream(
            model=model_to_use,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
