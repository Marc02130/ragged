"""Slice 5 unit: multipart ingest, magic bytes, quotas."""

from __future__ import annotations

import re
import threading
import uuid
from pathlib import Path

import pytest

from tests.paths import DOCUMENTS_ROUTER, ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice05,
    pytest.mark.skipif(not slice_ready(5), reason=skip_reason(5)),
]

SAMPLE_PDF = ROOT / "api" / "tests" / "fixtures" / "sample.pdf"
PATH_RE = re.compile(
    r"^[0-9a-f-]{36}/[0-9a-f-]{36}/[0-9a-f-]{36}\.(pdf|docx|txt|rtf)$"
)


@pytest.fixture(autouse=True)
def _upload_root(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "UPLOAD_ROOT", str(tmp_path))
    return tmp_path


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def _register_and_thread(client) -> tuple[dict, str]:
    user = client.post(
        "/api/auth/register", json={"email": _email(), "password": "correct-horse"}
    ).json()
    thread = client.post("/api/threads", json={"title": "Docs"}).json()
    return user, thread["id"]


def test_documents_router_is_sync_def() -> None:
    text = DOCUMENTS_ROUTER.read_text()
    assert "def upload_documents" in text
    assert "async def upload_documents" not in text
    assert "files" in text.lower()


def test_pdf_upload_ready_and_path_regex(client) -> None:
    from app import db
    from app.models import Document
    from sqlalchemy import select

    _, thread_id = _register_and_thread(client)
    pdf = SAMPLE_PDF.read_bytes()
    response = client.post(
        f"/api/threads/{thread_id}/documents",
        files=[("files", ("notes.pdf", pdf, "application/pdf"))],
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "ready"
    assert body[0]["chunk_count"] >= 1
    assert body[0]["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert "content" not in body[0]

    with db.SessionLocal() as session:
        row = session.scalar(select(Document).where(Document.id == uuid.UUID(body[0]["id"])))
    assert row is not None
    assert PATH_RE.match(row.file_path)


def test_delete_document_removes_row_chunks_and_file(client, tmp_path) -> None:
    from app import db
    from app.models import Document, VectorChunk
    from sqlalchemy import select

    _, thread_id = _register_and_thread(client)
    uploaded = client.post(
        f"/api/threads/{thread_id}/documents",
        files=[("files", ("notes.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
    )
    doc_id = uploaded.json()[0]["id"]
    with db.SessionLocal() as session:
        row = session.scalar(select(Document).where(Document.id == uuid.UUID(doc_id)))
        assert row is not None
        disk = tmp_path / row.file_path
        assert disk.is_file()

    deleted = client.delete(f"/api/threads/{thread_id}/documents/{doc_id}")
    assert deleted.status_code == 204
    listed = client.get(f"/api/threads/{thread_id}/documents")
    assert listed.json() == []
    with db.SessionLocal() as session:
        assert session.get(Document, uuid.UUID(doc_id)) is None
        leftover = session.scalars(
            select(VectorChunk).where(VectorChunk.document_id == uuid.UUID(doc_id))
        ).all()
        assert leftover == []
    assert not disk.is_file()


def test_delete_document_is_404_for_other_user(client) -> None:
    _, thread_id = _register_and_thread(client)
    uploaded = client.post(
        f"/api/threads/{thread_id}/documents",
        files=[("files", ("notes.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
    )
    doc_id = uploaded.json()[0]["id"]
    client.post("/api/auth/logout")
    _register_and_thread(client)
    assert client.delete(f"/api/threads/{thread_id}/documents/{doc_id}").status_code == 404


def test_exe_renamed_pdf_is_415_before_writes(client, tmp_path) -> None:
    from app import db
    from app.models import Document
    from sqlalchemy import select

    _, thread_id = _register_and_thread(client)
    payload = b"MZ" + b"\x00" * 64
    response = client.post(
        f"/api/threads/{thread_id}/documents",
        files=[("files", ("malware.pdf", payload, "application/pdf"))],
    )
    assert response.status_code == 415
    assert not any(p.is_file() for p in tmp_path.rglob("*"))
    with db.SessionLocal() as session:
        rows = session.scalars(
            select(Document).where(Document.thread_id == uuid.UUID(thread_id))
        ).all()
        assert rows == []


def test_file_over_10mb_is_413(client) -> None:
    _, thread_id = _register_and_thread(client)
    too_big = b"%PDF" + b"x" * (10 * 1024 * 1024)
    response = client.post(
        f"/api/threads/{thread_id}/documents",
        files=[("files", ("big.pdf", too_big, "application/pdf"))],
    )
    assert response.status_code == 413


def test_mixed_type_request_is_415_whole(client, tmp_path) -> None:
    from app import db
    from app.models import Document
    from sqlalchemy import select

    _, thread_id = _register_and_thread(client)
    pdf = SAMPLE_PDF.read_bytes()
    exe = b"MZ" + b"\x00" * 32
    response = client.post(
        f"/api/threads/{thread_id}/documents",
        files=[
            ("files", ("ok.pdf", pdf, "application/pdf")),
            ("files", ("bad.pdf", exe, "application/pdf")),
        ],
    )
    assert response.status_code == 415
    with db.SessionLocal() as session:
        rows = session.scalars(
            select(Document).where(Document.thread_id == uuid.UUID(thread_id))
        ).all()
        assert rows == []
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


def test_embed_error_marks_failed_not_ready(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service

    def boom(_texts: list[str], **_k: object) -> list[list[float]]:
        raise RuntimeError("openai down")

    monkeypatch.setattr(embeddings_service, "embed_texts", boom)
    _, thread_id = _register_and_thread(client)
    response = client.post(
        f"/api/threads/{thread_id}/documents",
        files=[("files", ("notes.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
    )
    assert response.status_code == 422
    assert "openai down" in response.json()["detail"].lower()


def test_concurrent_quota_does_not_exceed_20(client) -> None:
    from app import db
    from app.models import Document

    user, thread_id = _register_and_thread(client)
    with db.SessionLocal() as session:
        for index in range(19):
            session.add(
                Document(
                    thread_id=uuid.UUID(thread_id),
                    user_id=uuid.UUID(user["id"]),
                    file_path=f"{user['id']}/{thread_id}/{uuid.uuid4()}.txt",
                    file_name=f"{index}.txt",
                    file_size=1,
                    file_type="text/plain",
                    title=f"{index}.txt",
                    status="ready",
                )
            )
        session.commit()

    pdf = SAMPLE_PDF.read_bytes()
    codes: list[int] = []

    def upload() -> None:
        response = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[
                ("files", ("a.pdf", pdf, "application/pdf")),
                ("files", ("b.pdf", pdf, "application/pdf")),
            ],
        )
        codes.append(response.status_code)

    workers = [threading.Thread(target=upload) for _ in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    from sqlalchemy import func, select

    with db.SessionLocal() as session:
        count = session.scalar(
            select(func.count())
            .select_from(Document)
            .where(
                Document.thread_id == uuid.UUID(thread_id),
                Document.status.in_(("processing", "ready")),
            )
        )
    assert count <= 20
    assert 413 in codes or codes.count(201) == 1
