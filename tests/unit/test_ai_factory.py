from dataclasses import dataclass

import pytest

import src.infrastructure.ai.factory as factory_module
from src.infrastructure.ai.ollama_client import OllamaLLMClient
from src.infrastructure.ai.ollama_embedding_client import OllamaEmbeddingClient
from src.infrastructure.ai.openai_client import OpenAILLMClient
from src.infrastructure.ai.openai_embedding_client import OpenAIEmbeddingClient


@dataclass
class _FakeSettings:
    ai_provider: str


def test_get_llm_client_defaults_to_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_module, "get_settings", lambda: _FakeSettings("ollama"))

    assert isinstance(factory_module.get_llm_client(), OllamaLLMClient)


def test_get_llm_client_returns_openai_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_module, "get_settings", lambda: _FakeSettings("openai"))

    assert isinstance(factory_module.get_llm_client(), OpenAILLMClient)


def test_get_embedding_client_defaults_to_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_module, "get_settings", lambda: _FakeSettings("ollama"))

    assert isinstance(factory_module.get_embedding_client(), OllamaEmbeddingClient)


def test_get_embedding_client_returns_openai_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory_module, "get_settings", lambda: _FakeSettings("openai"))

    assert isinstance(factory_module.get_embedding_client(), OpenAIEmbeddingClient)
