import os
from flask import Blueprint, render_template, request, jsonify
from app.models.setting import AppSetting
from app.services.providers.factory import get_providers_status, get_provider
from app.services.providers.gemini import GeminiProvider, SUPPORTED_GEMINI_MODELS
from app.services.providers.ollama import OllamaProvider, DEFAULT_OLLAMA_FALLBACK_MODELS

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def settings_page():
    """Renders the Provider Configuration and Settings page."""
    provider_status = get_providers_status()
    active_provider = AppSetting.get("active_provider", "gemini")
    gemini_model = AppSetting.get("gemini_model", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    ollama_model = AppSetting.get("ollama_model", os.getenv("OLLAMA_MODEL", "llama3.2"))
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Discover installed Ollama models
    ollama_p = OllamaProvider(base_url=ollama_url)
    discovered_ollama_models = ollama_p.list_models()

    return render_template(
        "settings.html",
        provider_status=provider_status,
        active_provider=active_provider,
        gemini_model=gemini_model,
        ollama_model=ollama_model,
        ollama_url=ollama_url,
        gemini_models=SUPPORTED_GEMINI_MODELS,
        ollama_models=discovered_ollama_models or DEFAULT_OLLAMA_FALLBACK_MODELS,
        gemini_configured=bool(os.getenv("GEMINI_API_KEY", "").strip()),
    )


@settings_bp.route("/api/providers")
def api_providers():
    """Returns connectivity and model diagnostics for all AI providers."""
    return jsonify(get_providers_status())


@settings_bp.route("/api/providers/test", methods=["POST"])
def test_provider():
    """Runs an on-demand connectivity test for a specific provider."""
    data = request.get_json() or {}
    provider_name = data.get("provider", "gemini").lower()
    temp_key = data.get("api_key")  # For testing a key without persisting

    if provider_name == "gemini":
        prov = GeminiProvider(api_key=temp_key)
        res = prov.test_connection()
    elif provider_name == "ollama":
        base_url = data.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        prov = OllamaProvider(base_url=base_url)
        res = prov.test_connection()
    else:
        return jsonify({"success": False, "message": f"Unknown provider: {provider_name}"}), 400

    return jsonify(res.model_dump())


@settings_bp.route("/api/settings/save", methods=["POST"])
def save_settings():
    """Saves non-secret application preferences to the database."""
    data = request.get_json() or {}
    active_provider = data.get("active_provider")
    gemini_model = data.get("gemini_model")
    ollama_model = data.get("ollama_model")

    if active_provider and active_provider in ("gemini", "ollama"):
        AppSetting.set("active_provider", active_provider, "Active LLM provider")
    if gemini_model:
        AppSetting.set("gemini_model", gemini_model, "Selected Gemini model")
    if ollama_model:
        AppSetting.set("ollama_model", ollama_model, "Selected Ollama model")

    return jsonify({"success": True, "message": "Preferences saved successfully."})
