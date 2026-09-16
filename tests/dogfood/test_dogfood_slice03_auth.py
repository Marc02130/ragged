"""Slice 3 dogfood: register, call me, still logged in on the next request."""

import uuid

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice03,
    pytest.mark.skipif(not slice_ready(3), reason=skip_reason(3)),
]


def test_operator_registers_and_calls_me(compose_stack: str) -> None:
    email = f"dogfood-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=10.0) as client:
        registered = client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        assert registered.status_code == 201
        first = client.get("/api/auth/me")
        assert first.status_code == 200
        second = client.get("/api/auth/me")
        assert second.status_code == 200
        assert second.json()["email"] == email
        client.post("/api/auth/logout")
        after = client.get("/api/auth/me")
        assert after.status_code == 401
