"""Slice 4 unit: thread CRUD, archive, restore, delete, isolation."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from tests.paths import THREADS_ROUTER
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice04,
    pytest.mark.skipif(not slice_ready(4), reason=skip_reason(4)),
]


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def _register(client, email: str | None = None) -> dict:
    email = email or _email()
    response = client.post(
        "/api/auth/register", json={"email": email, "password": "correct-horse"}
    )
    assert response.status_code == 201
    return response.json()


def test_threads_router_has_archive_restore_delete() -> None:
    text = THREADS_ROUTER.read_text()
    assert "archive" in text
    assert "restore" in text
    assert "delete" in text.lower()


def test_create_list_archive_restore(client) -> None:
    _register(client)
    created = client.post("/api/threads", json={"title": "Q3 reports"})
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Q3 reports"
    assert body["status"] == "active"
    assert "user_id" not in body
    assert "thread_id" not in body
    thread_id = body["id"]

    listed = client.get("/api/threads")
    assert listed.status_code == 200
    assert any(t["id"] == thread_id for t in listed.json())

    archived = client.post(f"/api/threads/{thread_id}/archive")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert client.get("/api/threads").json() == []
    with_archived = client.get("/api/threads", params={"include_archived": True})
    assert any(t["id"] == thread_id for t in with_archived.json())

    restored = client.post(f"/api/threads/{thread_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["status"] == "active"
    assert any(t["id"] == thread_id for t in client.get("/api/threads").json())


def test_delete_is_204_with_cookie_only(client) -> None:
    _register(client)
    thread_id = client.post("/api/threads", json={"title": "gone"}).json()["id"]
    deleted = client.delete(f"/api/threads/{thread_id}")
    assert deleted.status_code == 204
    assert client.get("/api/threads").json() == []


def test_delete_removes_child_rows_and_upload_dir(client, tmp_path, monkeypatch) -> None:
    from app import db
    from app.config import settings
    from app.models import Conversation
    from sqlalchemy import select

    monkeypatch.setattr(settings, "UPLOAD_ROOT", str(tmp_path))
    user = _register(client)
    thread_id = client.post("/api/threads", json={"title": "with kids"}).json()["id"]
    upload = tmp_path / user["id"] / thread_id
    upload.mkdir(parents=True)
    (upload / "file.txt").write_text("x")

    with db.SessionLocal() as session:
        session.add(
            Conversation(
                thread_id=uuid.UUID(thread_id),
                user_id=uuid.UUID(user["id"]),
                role="user",
                content="hello",
            )
        )
        session.commit()

    assert client.delete(f"/api/threads/{thread_id}").status_code == 204
    with db.SessionLocal() as session:
        leftover = session.scalars(
            select(Conversation).where(Conversation.thread_id == uuid.UUID(thread_id))
        ).all()
    assert leftover == []
    assert not upload.exists()


def test_user_b_gets_404_on_user_a_thread(client) -> None:
    _register(client)
    thread_id = client.post("/api/threads", json={"title": "A only"}).json()["id"]
    client.post("/api/auth/logout")
    _register(client)
    assert client.get("/api/threads").json() == []
    assert client.post(f"/api/threads/{thread_id}/archive").status_code == 404
    assert client.post(f"/api/threads/{thread_id}/restore").status_code == 404
    assert client.delete(f"/api/threads/{thread_id}").status_code == 404
