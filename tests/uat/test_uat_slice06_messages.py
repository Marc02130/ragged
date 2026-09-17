"""Slice 6 UAT: canned refusal, no doubled history."""

import uuid

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice06,
    pytest.mark.skipif(not slice_ready(6), reason=skip_reason(6)),
]

CANNED = "I don't have that in your documents."


def test_empty_retrieval_returns_canned_refusal(compose_stack: str) -> None:
    email = f"uat-msg-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=30.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "empty"}).json()["id"]
        first = client.post(
            f"/api/threads/{thread_id}/messages", json={"content": "what is in here?"}
        )
        assert first.status_code == 200
        assert first.json()["assistant_message"]["content"] == CANNED
        assert "response" not in first.json()
        second = client.post(
            f"/api/threads/{thread_id}/messages", json={"content": "and now?"}
        )
        assert second.status_code == 200
        listed = client.get(f"/api/threads/{thread_id}/messages")
        assert len(listed.json()) == 4
