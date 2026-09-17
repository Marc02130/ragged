"""UAT: per-user LLM keys on the live API. Secrets never leave the server."""

import uuid

import httpx
import pytest

pytestmark = [pytest.mark.uat]


def test_settings_roundtrip_hides_secrets(compose_stack: str) -> None:
    email = f"uat-llm-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=20.0) as client:
        assert (
            client.post(
                "/api/auth/register",
                json={"email": email, "password": "correct-horse-battery"},
            ).status_code
            == 201
        )
        got = client.get("/api/settings/llm")
        assert got.status_code == 200
        body = got.json()
        assert "openai_api_key" not in body
        assert body["chat_models"]["xai"] == "grok-4.5"

        saved = client.put(
            "/api/settings/llm",
            json={
                "xai_api_key": "xai-uat-live-looking-key",
                "chat_provider": "xai",
            },
        )
        assert saved.status_code == 200
        assert saved.json()["xai"]["configured"] is True
        assert saved.json()["chat_provider"] == "xai"
        assert "xai-uat-live" not in saved.text

        denied = client.put("/api/settings/llm", json={"chat_provider": "anthropic"})
        assert denied.status_code == 422
