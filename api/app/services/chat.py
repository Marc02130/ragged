from __future__ import annotations

import httpx
from openai import OpenAI

from app.config import settings
from app.models import User, UserLlmSettings
from app.services.llm_keys import CHAT_MODELS, resolve_key


def complete(prompt: str, user: User, llm: UserLlmSettings | None) -> str:
    provider = (llm.chat_provider if llm else "openai")
    key = resolve_key(llm, provider)
    if not key:
        raise PermissionError(f"Configure an API key for {provider} in Settings")
    model = CHAT_MODELS[provider]
    if provider == "anthropic":
        return _anthropic(prompt, key, model)
    if provider == "xai":
        client = OpenAI(
            api_key=key,
            base_url=settings.XAI_BASE_URL,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
        return _openai_chat(client, model, prompt)
    client = OpenAI(api_key=key, timeout=settings.OPENAI_TIMEOUT_SECONDS)
    return _openai_chat(client, model, prompt)


def _openai_chat(client: OpenAI, model: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=settings.OPENAI_TEMPERATURE,
        max_tokens=settings.OPENAI_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def _anthropic(prompt: str, key: str, model: str) -> str:
    with httpx.Client(timeout=settings.OPENAI_TIMEOUT_SECONDS) as client:
        response = client.post(
            settings.ANTHROPIC_API_URL,
            headers={
                "x-api-key": key,
                "anthropic-version": settings.ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": settings.OPENAI_MAX_TOKENS,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
    blocks = data.get("content") or []
    texts = [block.get("text", "") for block in blocks if block.get("type") == "text"]
    return "".join(texts)
