"""Dogfood: canned replies do not list junk sources in the API envelope."""

import uuid

import httpx
import pytest

pytestmark = [pytest.mark.dogfood]


def test_canned_has_empty_sources(compose_stack: str) -> None:
    email = f"dogfood-junk-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=30.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "empty"}).json()["id"]
        asked = client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "what hypotheses have the best evidence"},
        )
        assert asked.status_code == 200
        body = asked.json()["assistant_message"]
        assert body["content"].strip() == "I don't have that in your documents."
        assert body.get("sources") == []
