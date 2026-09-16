"""Slice 4 dogfood: create, archive, restore, delete a thread."""

import uuid

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice04,
    pytest.mark.skipif(not slice_ready(4), reason=skip_reason(4)),
]


def test_operator_thread_lifecycle(compose_stack: str) -> None:
    email = f"dogfood-t-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=10.0) as client:
        assert (
            client.post(
                "/api/auth/register",
                json={"email": email, "password": "correct-horse-battery"},
            ).status_code
            == 201
        )
        created = client.post("/api/threads", json={"title": "Lab notes"})
        assert created.status_code == 201
        thread_id = created.json()["id"]
        assert any(t["id"] == thread_id for t in client.get("/api/threads").json())

        archived = client.post(f"/api/threads/{thread_id}/archive")
        assert archived.status_code == 200
        assert archived.json()["status"] == "archived"
        assert client.get("/api/threads").json() == []
        restored = client.post(f"/api/threads/{thread_id}/restore")
        assert restored.json()["status"] == "active"

        deleted = client.delete(f"/api/threads/{thread_id}")
        assert deleted.status_code == 204
        assert client.get("/api/threads").json() == []
