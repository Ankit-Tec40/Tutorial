import os
import time
from typing import Optional, Dict, Any
from flask import has_app_context
from app.services.providers.base import BaseLLMProvider
from app.services.providers.gemini import GeminiProvider, SUPPORTED_GEMINI_MODELS
from app.services.providers.ollama import OllamaProvider, DEFAULT_OLLAMA_FALLBACK_MODELS
from app.models.setting import AppSetting

_STATUS_CACHE: Dict[str, Any] = {}
_STATUS_CACHE_TIME: float = 0.0
_CACHE_TTL_SECONDS: float = 10.0


def _get_setting_safe(key: str, default: str) -> str:
    """Safely retrieves a setting if in application context, else returns default."""
    if has_app_context():
        try:
            val = AppSetting.get(key)
            if val:
                return val
        except Exception:
            pass
    return default


def get_provider(
    provider_name: Optional[str] = None, 
    model_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> BaseLLMProvider:
    """Factory to instantiate the appropriate provider instance."""
    # Determine provider name
    if not provider_name:
        provider_name = _get_setting_safe("active_provider", "gemini")

    provider_name = provider_name.lower().strip()

    if provider_name == "ollama":
        target_model = model_name or _get_setting_safe("ollama_model", os.getenv("OLLAMA_MODEL", "llama3.2"))
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaProvider(base_url=base_url, model_name=target_model)
    elif provider_name == "gemini":
        target_model = model_name or _get_setting_safe("gemini_model", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        return GeminiProvider(api_key=api_key, model_name=target_model)
    else:
        raise ValueError(f"Unsupported AI provider: '{provider_name}'. Supported: 'gemini', 'ollama'.")


def get_providers_status(force_refresh: bool = False) -> Dict[str, Any]:
    """Tests both providers and returns comprehensive connectivity diagnostics with a 10s TTL cache."""
    global _STATUS_CACHE, _STATUS_CACHE_TIME

    now = time.time()
    if not force_refresh and _STATUS_CACHE and (now - _STATUS_CACHE_TIME < _CACHE_TTL_SECONDS):
        return _STATUS_CACHE

    gemini = GeminiProvider()
    ollama = OllamaProvider()

    gemini_status = gemini.test_connection()
    ollama_status = ollama.test_connection()

    active_provider = _get_setting_safe("active_provider", "gemini")

    status = {
        "active_provider": active_provider,
        "gemini": gemini_status.model_dump(),
        "ollama": ollama_status.model_dump(),
    }

    _STATUS_CACHE = status
    _STATUS_CACHE_TIME = now
    return status
