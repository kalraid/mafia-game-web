from __future__ import annotations

import os
from typing import Any


def _llm_provider() -> str:
    raw = os.getenv("MAFIA_LLM_PROVIDER", "anthropic").strip().lower()
    return "azure" if raw == "azure" else "anthropic"


def is_llm_enabled() -> bool:
    """MAFIA_USE_LLM=0 이면 False."""
    return os.getenv("MAFIA_USE_LLM", "1").strip().lower() not in {"0", "false", "no"}


def is_llm_credentials_available() -> bool:
    """LLM 사용이 켜져 있고, 선택된 Provider에 필요한 자격 증명이 있는지 (매 호출 시 env 재조회)."""
    if not is_llm_enabled():
        return False
    if _llm_provider() == "azure":
        return bool(
            os.getenv("AOAI_API_KEY", "").strip()
            and os.getenv("AOAI_ENDPOINT", "").strip()
            and os.getenv("AOAI_DEPLOY_GPT4O", "").strip()
        )
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


def get_chat_llm(temperature: float = 0) -> Any | None:
    """
    Provider에 따라 LangChain Chat 모델을 반환한다.
    사용 불가 시 None → 호출부에서 Fallback 처리.
    """
    if not is_llm_enabled():
        return None

    if _llm_provider() == "azure":
        api_key = os.getenv("AOAI_API_KEY", "").strip()
        endpoint = os.getenv("AOAI_ENDPOINT", "").strip()
        deploy = os.getenv("AOAI_DEPLOY_GPT4O", "").strip()
        api_version = os.getenv("AOAI_API_VERSION", "2024-02-01").strip()
        if not (api_key and endpoint and deploy):
            return None
        try:
            from langchain_openai import AzureChatOpenAI
        except ImportError:
            return None
        return AzureChatOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            azure_deployment=deploy,
            openai_api_version=api_version,
            temperature=temperature,
        )

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4")
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        return None
    return ChatAnthropic(
        model=model_name,
        api_key=api_key,
        temperature=temperature,
    )


def get_llm_provider_health() -> str:
    """
    /health용: anthropic | azure | disabled | fallback
    """
    if not is_llm_enabled():
        return "disabled"
    if _llm_provider() == "azure":
        if (
            os.getenv("AOAI_API_KEY", "").strip()
            and os.getenv("AOAI_ENDPOINT", "").strip()
            and os.getenv("AOAI_DEPLOY_GPT4O", "").strip()
        ):
            return "azure"
        return "fallback"
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    return "fallback"


# 하위 호환·문서용 (정적 스냅샷이 필요할 때만 사용)
LLM_PROVIDER: str = _llm_provider()

LLM_CONFIG: dict[str, str] = {
    "provider": LLM_PROVIDER,
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", "").strip(),
    "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4"),
    "aoai_endpoint": os.getenv("AOAI_ENDPOINT", "").strip(),
    "aoai_api_key": os.getenv("AOAI_API_KEY", "").strip(),
    "aoai_api_version": os.getenv("AOAI_API_VERSION", "2024-02-01").strip(),
    "aoai_deploy_chat": os.getenv("AOAI_DEPLOY_GPT4O", "").strip(),
    "aoai_deploy_mini": os.getenv("AOAI_DEPLOY_GPT4O_MINI", "").strip(),
    "aoai_deploy_embed": os.getenv("AOAI_DEPLOY_EMBED_3_LARGE", "").strip(),
}
