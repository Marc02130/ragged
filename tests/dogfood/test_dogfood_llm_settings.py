"""Dogfood: API keys UI is in the SPA; settings endpoint works after register."""

import re
import uuid

import httpx
import pytest

pytestmark = [pytest.mark.dogfood]


def test_operator_sees_api_keys_and_grok(compose_stack: str) -> None:
    home = httpx.get(f"{compose_stack}/", timeout=10.0)
    js_names = re.findall(r"/assets/[\w.-]+\.js", home.text)
    assert js_names
    bundle = httpx.get(f"{compose_stack}{js_names[0]}", timeout=10.0).text
    assert "API keys" in bundle
    assert "Grok" in bundle
    assert "Anthropic" in bundle or "Claude" in bundle

    email = f"dogfood-llm-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=20.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        body = client.get("/api/settings/llm").json()
        assert "chat_provider" in body
        assert "openai_api_key" not in body
