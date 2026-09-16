"""Slice 4 UAT: isolation — user B cannot see user A's thread."""

import uuid

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice04,
    pytest.mark.skipif(not slice_ready(4), reason=skip_reason(4)),
]


def test_cross_user_thread_is_404(compose_stack: str) -> None:
    password = "correct-horse-battery"
    with httpx.Client(base_url=compose_stack, timeout=10.0) as alice:
        alice.post(
            "/api/auth/register",
            json={"email": f"alice-{uuid.uuid4().hex[:8]}@example.com", "password": password},
        )
        created = alice.post("/api/threads", json={"title": "Alice secret"})
        assert created.status_code == 201
        thread_id = created.json()["id"]

    with httpx.Client(base_url=compose_stack, timeout=10.0) as bob:
        bob.post(
            "/api/auth/register",
            json={"email": f"bob-{uuid.uuid4().hex[:8]}@example.com", "password": password},
        )
        assert bob.get("/api/threads").json() == []
        assert bob.post(f"/api/threads/{thread_id}/archive").status_code == 404
        assert bob.delete(f"/api/threads/{thread_id}").status_code == 404

