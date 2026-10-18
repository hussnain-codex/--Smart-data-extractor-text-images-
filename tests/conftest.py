import pytest


@pytest.fixture(autouse=True)
def isolate_gemini_settings(monkeypatch):
    """Keep model settings from the local .env out of the unit tests."""
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_FALLBACK_MODELS", raising=False)
