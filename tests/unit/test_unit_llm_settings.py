"""Per-user LLM keys: store encrypted, never return secrets, select chat provider."""

from __future__ import annotations

import uuid

import pytest

pytestmark = [pytest.mark.unit]


def _email() -> str:
    return f"llm-{uuid.uuid4().hex[:12]}@example.com"


def _register(client) -> None:
    client.post("/api/auth/register", json={"email": _email(), "password": "correct-horse"})


def test_get_settings_has_no_secrets(client) -> None:
    _register(client)
    response = client.get("/api/settings/llm")
    assert response.status_code == 200
    body = response.json()
    assert "openai_api_key" not in body
    assert "xai_api_key" not in body
    assert set(body) >= {"openai", "xai", "anthropic", "chat_provider", "chat_models"}
    assert body["chat_models"]["xai"] == "grok-4.5"
    assert body["chat_models"]["anthropic"] == "claude-sonnet-4-5"


def test_put_keys_and_select_provider(client) -> None:
    _register(client)
    saved = client.put(
        "/api/settings/llm",
        json={
            "openai_api_key": "sk-live-openai-not-a-placeholder-key",
            "xai_api_key": "xai-live-key-for-tests",
            "anthropic_api_key": "sk-ant-live-key-for-tests",
            "chat_provider": "xai",
        },
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["openai"]["configured"] is True
    assert body["xai"]["configured"] is True
    assert body["anthropic"]["configured"] is True
    assert body["chat_provider"] == "xai"
    assert "xai-live-key" not in saved.text

    again = client.get("/api/settings/llm")
    assert again.json()["chat_provider"] == "xai"
    assert "xai-live-key" not in again.text


def test_cannot_select_provider_without_key(client) -> None:
    _register(client)
    response = client.put("/api/settings/llm", json={"chat_provider": "anthropic"})
    assert response.status_code == 422


def test_clear_key(client) -> None:
    _register(client)
    client.put("/api/settings/llm", json={"anthropic_api_key": "sk-ant-live-key-for-tests"})
    cleared = client.put("/api/settings/llm", json={"anthropic_api_key": ""})
    assert cleared.status_code == 200
    assert cleared.json()["anthropic"]["configured"] is False
