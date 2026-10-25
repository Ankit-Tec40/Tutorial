from unittest.mock import patch, MagicMock
from app.services.providers.gemini import GeminiProvider
from app.services.providers.ollama import OllamaProvider
from app.services.providers.factory import get_provider, get_providers_status


def test_gemini_missing_key_behavior():
    """GeminiProvider gracefully handles missing API key without crashing."""
    provider = GeminiProvider(api_key="")
    result = provider.test_connection()
    assert result.success is False
    assert result.error_code == "MISSING_API_KEY"
    assert "GEMINI_API_KEY" in result.message


def test_ollama_offline_behavior():
    """OllamaProvider gracefully detects offline server without unhandled network exceptions."""
    provider = OllamaProvider(base_url="http://127.0.0.1:9999")  # Unreachable port
    result = provider.test_connection()
    assert result.success is False
    assert result.error_code == "OLLAMA_NOT_RUNNING"
    assert "ollama serve" in result.setup_instructions


@patch("requests.get")
def test_ollama_mocked_connection(mock_get):
    """Verifies Ollama model discovery with mocked HTTP response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "llama3.2:latest"}, {"name": "nomic-embed-text:latest"}]
    }
    mock_get.return_value = mock_resp

    provider = OllamaProvider()
    result = provider.test_connection()
    assert result.success is True
    assert "llama3.2:latest" in result.available_models


def test_provider_factory():
    """Verifies provider instantiation by name."""
    gemini_p = get_provider("gemini")
    assert gemini_p.name == "gemini"

    ollama_p = get_provider("ollama")
    assert ollama_p.name == "ollama"
