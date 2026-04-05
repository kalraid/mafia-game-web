from __future__ import annotations

import pytest

from backend.config import (
    get_chat_llm,
    get_llm_provider_health,
    is_llm_credentials_available,
    is_llm_enabled,
)


def test_is_llm_enabled_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "0")
    assert is_llm_enabled() is False
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    assert is_llm_enabled() is True


def test_get_llm_provider_health_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "0")
    assert get_llm_provider_health() == "disabled"


def test_get_llm_provider_health_anthropic_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("MAFIA_LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert get_llm_provider_health() == "fallback"


def test_get_llm_provider_health_anthropic_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("MAFIA_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")
    assert get_llm_provider_health() == "anthropic"


def test_get_llm_provider_health_azure_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("MAFIA_LLM_PROVIDER", "azure")
    monkeypatch.setenv("AOAI_API_KEY", "k")
    monkeypatch.setenv("AOAI_ENDPOINT", "https://x.openai.azure.com")
    monkeypatch.setenv("AOAI_DEPLOY_GPT4O", "gpt-4o")
    assert get_llm_provider_health() == "azure"


def test_is_llm_credentials_available_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("MAFIA_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert is_llm_credentials_available() is True


def test_get_chat_llm_returns_none_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "0")
    assert get_chat_llm() is None
