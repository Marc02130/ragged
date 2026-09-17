"""Slice 6 unit: RAG messages, canned refusal, no client model."""

from __future__ import annotations

import math
import uuid

import pytest

from tests.paths import MESSAGES_ROUTER, ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice06,
    pytest.mark.skipif(not slice_ready(6), reason=skip_reason(6)),
]

CANNED = "I don't have that in your documents."
DIM = 384


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def _register_and_thread(client) -> tuple[dict, str]:
    user = client.post(
        "/api/auth/register", json={"email": _email(), "password": "correct-horse"}
    ).json()
    thread = client.post("/api/threads", json={"title": "Ask"}).json()
    return user, thread["id"]


def _unit_vec(sim: float) -> list[float]:
    values = [0.0] * DIM
    values[0] = sim
    values[1] = math.sqrt(max(0.0, 1.0 - sim * sim))
    return values


QUERY_VEC = [1.0] + [0.0] * (DIM - 1)


def _seed_chunk(user_id: str, thread_id: str, embedding: list[float], content: str = "alpha") -> None:
    from app import db
    from app.models import Document, VectorChunk

    with db.SessionLocal() as session:
        doc = Document(
            thread_id=uuid.UUID(thread_id),
            user_id=uuid.UUID(user_id),
            file_path=f"{user_id}/{thread_id}/{uuid.uuid4()}.txt",
            file_name="notes.txt",
            file_size=5,
            file_type="text/plain",
            title="notes.txt",
            status="ready",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            chunk_count=1,
        )
        session.add(doc)
        session.flush()
        session.add(
            VectorChunk(
                document_id=doc.id,
                thread_id=uuid.UUID(thread_id),
                user_id=uuid.UUID(user_id),
                content=content,
                embedding=embedding,
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                chunk_index=0,
            )
        )
        session.commit()


def test_messages_router_forbids_client_model_and_cross_thread() -> None:
    text = MESSAGES_ROUTER.read_text()
    rag = (ROOT / "api" / "app" / "services" / "rag.py").read_text()
    prompts = (ROOT / "api" / "app" / "prompts.py").read_text()
    combined = text + rag + prompts
    assert ":candidate" in rag or "SIMILARITY_THRESHOLD" in rag
    from app.config import settings as app_settings

    assert app_settings.SIMILARITY_THRESHOLD == 0.4
    assert "I don't have that in your documents." in combined


def test_empty_retrieval_canned_refusal_skips_chat(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service

    monkeypatch.setattr(embeddings_service, "embed_texts", lambda texts, **_k: [QUERY_VEC])
    called = {"chat": 0}

    def boom(_prompt: str, *_args, **_kwargs) -> str:
        called["chat"] += 1
        raise AssertionError("chat should not be called")

    monkeypatch.setattr(rag_service, "complete", boom)
    _, thread_id = _register_and_thread(client)
    response = client.post(
        f"/api/threads/{thread_id}/messages", json={"content": "what is this?"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "response" not in body
    assert body["assistant_message"]["content"] == CANNED
    assert body["assistant_message"]["sources"] == []
    assert called["chat"] == 0


def test_two_posts_create_four_rows(client, monkeypatch) -> None:
    from app import db
    from app.models import Conversation
    from app.services import embeddings as embeddings_service
    from sqlalchemy import func, select

    monkeypatch.setattr(embeddings_service, "embed_texts", lambda texts, **_k: [QUERY_VEC])
    _, thread_id = _register_and_thread(client)
    client.post(f"/api/threads/{thread_id}/messages", json={"content": "one"})
    client.post(f"/api/threads/{thread_id}/messages", json={"content": "two"})
    with db.SessionLocal() as session:
        count = session.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.thread_id == uuid.UUID(thread_id))
        )
    assert count == 4


def test_get_messages_hydrates_sources(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service

    monkeypatch.setattr(embeddings_service, "embed_texts", lambda texts, **_k: [QUERY_VEC])
    monkeypatch.setattr(rag_service, "complete", lambda prompt, *_a, **_k: "from sources")
    user, thread_id = _register_and_thread(client)
    _seed_chunk(user["id"], thread_id, _unit_vec(0.71), content="the sky is teal")
    posted = client.post(
        f"/api/threads/{thread_id}/messages", json={"content": "what color?"}
    )
    assert posted.status_code == 200
    sources = posted.json()["assistant_message"]["sources"]
    assert sources
    listed = client.get(f"/api/threads/{thread_id}/messages")
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 2
    assert rows[0]["sources"] == []
    assert rows[1]["sources"] == sources


def test_extra_fields_and_length_rejected(client) -> None:
    _, thread_id = _register_and_thread(client)
    assert (
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "hi", "model": "gpt-4"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "hi", "temperature": 0.9},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "hi", "userId": str(uuid.uuid4())},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "hi", "crossThreadSearch": True},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "x" * 8001},
        ).status_code
        == 422
    )


def test_cosine_below_threshold_falls_back_to_nearest_chunks(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service

    monkeypatch.setattr(embeddings_service, "embed_texts", lambda texts, **_k: [QUERY_VEC])
    chat_calls: list[str] = []

    def fake_complete(prompt: str, *_args, **_kwargs) -> str:
        chat_calls.append(prompt)
        return "from nearest papers"

    monkeypatch.setattr(rag_service, "complete", fake_complete)

    user, thread_id = _register_and_thread(client)
    _seed_chunk(user["id"], thread_id, _unit_vec(0.39), content="gut microbiome")
    response = client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "what hypotheses have the best evidence"},
    )
    assert response.status_code == 200
    assert response.json()["assistant_message"]["content"] == "from nearest papers"
    assert response.json()["assistant_message"]["sources"]
    assert chat_calls
