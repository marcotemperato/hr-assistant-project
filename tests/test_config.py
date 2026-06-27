import pytest

from config import Config


def test_validate_api_keys_rejects_placeholder(monkeypatch):
    monkeypatch.setattr(Config, "OPENAI_KEY", "sk-your-openai-key")
    monkeypatch.setattr(Config, "AI_API_KEY", "sk-your-openai-key")

    with pytest.raises(ValueError, match="placeholder"):
        Config.validate_api_keys()


def test_validate_api_keys_accepts_real_keys(monkeypatch):
    monkeypatch.setattr(Config, "OPENAI_KEY", "sk-proj-real-key-example")
    monkeypatch.setattr(Config, "AI_API_KEY", "sk-proj-real-key-example")

    Config.validate_api_keys()
