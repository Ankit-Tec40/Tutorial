import os
import time
import json
import logging
from typing import List, Dict, Any, Generator, Optional
import requests
from app.services.providers.base import BaseLLMProvider, ProviderResponse, ConnectionTestResult

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_FALLBACK_MODELS = [
    "llama3.2",
    "llama3.1",
    "mistral",
    "qwen2.5",
    "phi3",
    "nomic-embed-text",
]


class OllamaProvider(BaseLLMProvider):
    """Local LLM provider using Ollama's HTTP API."""

    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        selected_model = model_name or os.getenv("OLLAMA_MODEL", "llama3.2")
        super().__init__(model_name=selected_model)
        self.timeout = 60  # seconds

    @property
    def name(self) -> str:
        return "ollama"

    def test_connection(self) -> ConnectionTestResult:
        """Tests connectivity and checks installed models in Ollama."""
        start_time = time.perf_counter()
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if resp.status_code == 200:
                data = resp.json()
                raw_models = data.get("models", [])
                models = [m.get("name") for m in raw_models if m.get("name")]

                if not models:
                    return ConnectionTestResult(
                        success=True,
                        provider="ollama",
                        message=f"Connected to Ollama at {self.base_url}, but no local models are installed yet.",
                        available_models=DEFAULT_OLLAMA_FALLBACK_MODELS,
                        latency_ms=round(elapsed_ms, 2),
                        setup_instructions="Pull a model in your terminal using: ollama pull llama3.2",
                    )

                return ConnectionTestResult(
                    success=True,
                    provider="ollama",
                    message=f"Connected to Ollama at {self.base_url}. Found {len(models)} installed model(s).",
                    available_models=models,
                    latency_ms=round(elapsed_ms, 2),
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    provider="ollama",
                    message=f"Ollama returned HTTP {resp.status_code}: {resp.text}",
                    available_models=DEFAULT_OLLAMA_FALLBACK_MODELS,
                    latency_ms=round(elapsed_ms, 2),
                    error_code="HTTP_ERROR",
                    setup_instructions="Check your Ollama service logs and verify the base URL in .env.",
                )
        except requests.exceptions.ConnectionError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ConnectionTestResult(
                success=False,
                provider="ollama",
                message=f"Could not connect to Ollama at {self.base_url}. Service is not reachable.",
                available_models=DEFAULT_OLLAMA_FALLBACK_MODELS,
                latency_ms=round(elapsed_ms, 2),
                error_code="OLLAMA_NOT_RUNNING",
                setup_instructions="Ensure Ollama is installed and running. Start the service with 'ollama serve' or open the Ollama desktop app.",
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("Ollama connection test error: %s", e)
            return ConnectionTestResult(
                success=False,
                provider="ollama",
                message=f"Ollama connection error: {str(e)}",
                available_models=DEFAULT_OLLAMA_FALLBACK_MODELS,
                latency_ms=round(elapsed_ms, 2),
                error_code="UNKNOWN_ERROR",
            )

    def list_models(self) -> List[str]:
        """Dynamically discovers installed models in Ollama, falling back to common options."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                if models:
                    return models
        except Exception as e:
            logger.debug("Could not query Ollama tags: %s", e)
        return DEFAULT_OLLAMA_FALLBACK_MODELS

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ProviderResponse:
        """Generates a synchronous completion via Ollama."""
        model_to_use = self.model_name or "llama3.2"
        payload: Dict[str, Any] = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": float(temperature),
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if max_tokens:
            payload["options"]["num_predict"] = int(max_tokens)
        if json_mode:
            payload["format"] = "json"

        start_time = time.perf_counter()
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if resp.status_code != 200:
                error_msg = resp.text
                if "model" in error_msg.lower() and "not found" in error_msg.lower():
                    raise RuntimeError(
                        f"Model '{model_to_use}' is not installed in Ollama. Run: ollama pull {model_to_use}"
                    )
                raise RuntimeError(f"Ollama HTTP {resp.status_code}: {error_msg}")

            data = resp.json()
            content = data.get("response", "")
            p_tokens = data.get("prompt_eval_count")
            c_tokens = data.get("eval_count")
            t_tokens = (p_tokens or 0) + (c_tokens or 0) if (p_tokens or c_tokens) else None

            return ProviderResponse(
                content=content,
                model=model_to_use,
                provider="ollama",
                latency_ms=round(elapsed_ms, 2),
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
            )
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. Please ensure Ollama is running ('ollama serve')."
            )
        except Exception as e:
            logger.error("Ollama generate call failed: %s", e)
            raise

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Streams conversation response from Ollama line by line."""
        model_to_use = self.model_name or "llama3.2"

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            formatted_messages.append({
                "role": m.get("role", "user"),
                "content": m.get("content", ""),
            })

        payload = {
            "model": model_to_use,
            "messages": formatted_messages,
            "stream": True,
            "options": {
                "temperature": float(temperature),
            },
        }
        if max_tokens:
            payload["options"]["num_predict"] = int(max_tokens)

        try:
            with requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=self.timeout,
            ) as response:
                if response.status_code != 200:
                    yield f"Error from Ollama ({response.status_code}): {response.text}"
                    return

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode("utf-8"))
                            msg_chunk = chunk.get("message", {}).get("content", "")
                            if msg_chunk:
                                yield msg_chunk
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.ConnectionError:
            yield f"Error: Ollama is unreachable at {self.base_url}. Please start Ollama."
        except Exception as e:
            yield f"Error during Ollama stream: {str(e)}"

    def embed(self, text: str, model_name: Optional[str] = None) -> List[float]:
        """Generates embeddings using Ollama's embedding endpoint."""
        embed_model = model_name or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        try:
            resp = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": embed_model, "prompt": text},
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json().get("embedding", [])
            else:
                logger.warning("Ollama embed error %s: %s", resp.status_code, resp.text)
                return []
        except Exception as e:
            logger.warning("Ollama embedding failed: %s", e)
            return []
