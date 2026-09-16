from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user, get_owned_thread
from app.models import Document, Thread, User, VectorChunk
from app.schemas import DocumentOut
from app.services import chunk as chunk_service
from app.services import embeddings as embeddings_service
from app.services import extract as extract_service
from app.services import files as files_service
from app.services.extract import KIND_MIME, UnsupportedFileType

router = APIRouter(tags=["documents"])

STALE_PROCESSING = timedelta(seconds=100)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _mark_stale_failed(session: Session, thread: Thread) -> None:
    cutoff = _now() - STALE_PROCESSING
    rows = session.scalars(
        select(Document).where(
            Document.thread_id == thread.id,
            Document.status == "processing",
            Document.updated_at < cutoff,
        )
    ).all()
    for doc in rows:
        doc.status = "failed"
        doc.chunk_count = 0
        doc.error_message = doc.error_message or "ingest timed out"
        session.execute(delete(VectorChunk).where(VectorChunk.document_id == doc.id))
    if rows:
        session.commit()


def _refresh_document_count(session: Session, thread: Thread) -> None:
    thread.document_count = session.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.thread_id == thread.id, Document.status == "ready")
    ) or 0
    thread.last_activity_at = _now()
    thread.updated_at = _now()


def _fail_document(session: Session, doc: Document, message: str) -> None:
    doc.status = "failed"
    doc.chunk_count = 0
    doc.error_message = message
    session.execute(delete(VectorChunk).where(VectorChunk.document_id == doc.id))


@router.get("/threads/{thread_id}/documents", response_model=list[DocumentOut])
def list_documents(
    thread: Thread = Depends(get_owned_thread),
    session: Session = Depends(get_db),
) -> list[Document]:
    _mark_stale_failed(session, thread)
    return list(
        session.scalars(
            select(Document)
            .where(Document.thread_id == thread.id)
            .order_by(Document.created_at)
        )
    )


@router.get("/threads/{thread_id}/documents/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: UUID,
    thread: Thread = Depends(get_owned_thread),
    session: Session = Depends(get_db),
) -> Document:
    _mark_stale_failed(session, thread)
    doc = session.get(Document, doc_id)
    if doc is None or doc.thread_id != thread.id or doc.user_id != thread.user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post(
    "/threads/{thread_id}/documents",
    response_model=list[DocumentOut],
    status_code=status.HTTP_201_CREATED,
)
def upload_documents(
    request: Request,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    thread: Thread = Depends(get_owned_thread),
    session: Session = Depends(get_db),
) -> list[Document]:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_UPLOAD_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Request body too large")
    if not files:
        raise HTTPException(status_code=422, detail="No files uploaded")

    payloads: list[tuple[str, bytes, str]] = []
    for upload in files:
        data = upload.file.read()
        if len(data) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        try:
            kind = extract_service.detect_kind(data)
        except UnsupportedFileType:
            raise HTTPException(status_code=415, detail="Unsupported file type") from None
        payloads.append((files_service.display_name(upload.filename), data, kind))

    locked = session.execute(
        select(Thread)
        .where(Thread.id == thread.id, Thread.user_id == user.id)
        .with_for_update()
    ).scalar_one()

    existing_count = session.scalar(
        select(func.count())
        .select_from(Document)
        .where(
            Document.thread_id == locked.id,
            Document.status.in_(("processing", "ready")),
        )
    ) or 0
    existing_size = session.scalar(
        select(func.coalesce(func.sum(Document.file_size), 0)).where(
            Document.thread_id == locked.id,
            Document.status.in_(("processing", "ready")),
        )
    ) or 0
    user_size = session.scalar(
        select(func.coalesce(func.sum(Document.file_size), 0)).where(
            Document.user_id == user.id,
            Document.status.in_(("processing", "ready")),
        )
    ) or 0
    batch_size = sum(len(data) for _, data, _ in payloads)
    if existing_count + len(payloads) > settings.MAX_FILES_PER_THREAD:
        raise HTTPException(status_code=413, detail="Thread file count quota exceeded")
    if existing_size + batch_size > settings.MAX_TOTAL_SIZE_PER_THREAD:
        raise HTTPException(status_code=413, detail="Thread size quota exceeded")
    if user_size + batch_size > settings.MAX_TOTAL_SIZE_PER_USER:
        raise HTTPException(status_code=413, detail="User size quota exceeded")

    created: list[Document] = []
    try:
        for name, data, kind in payloads:
            relative = files_service.new_relative_path(user.id, locked.id, kind)
            files_service.write_bytes(relative, data)
            doc = Document(
                thread_id=locked.id,
                user_id=user.id,
                file_path=relative,
                file_name=name,
                file_size=len(data),
                file_type=KIND_MIME[kind],
                title=name,
                content=None,
                status="processing",
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
            created.append(doc)
            try:
                _ingest_one(session, doc, data, kind)
            except Exception as exc:  # noqa: BLE001 — per-file failure
                session.rollback()
                doc = session.get(Document, doc.id)
                if doc is not None:
                    _fail_document(session, doc, str(exc))
                    session.commit()
        _refresh_document_count(session, locked)
        session.commit()
    finally:
        for doc in created:
            row = session.get(Document, doc.id)
            if row is not None and row.status == "processing":
                _fail_document(session, row, "ingest interrupted")
        session.commit()

    return [session.get(Document, doc.id) for doc in created]


def _ingest_one(session: Session, doc: Document, data: bytes, kind: str) -> None:
    text = extract_service.extract_text(data, kind)
    if not text.strip():
        _fail_document(session, doc, "empty extract")
        session.commit()
        return
    if len(text) > settings.MAX_CONTENT_CHARS:
        _fail_document(session, doc, "extracted text too large")
        session.commit()
        return
    pieces = chunk_service.split_text(
        text, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP
    )
    if len(pieces) > settings.MAX_CHUNKS_PER_DOCUMENT:
        _fail_document(session, doc, "too many chunks")
        session.commit()
        return
    vectors = embeddings_service.embed_texts(pieces)
    for index, (piece, vector) in enumerate(zip(pieces, vectors, strict=True)):
        session.add(
            VectorChunk(
                document_id=doc.id,
                thread_id=doc.thread_id,
                user_id=doc.user_id,
                content=piece,
                embedding=vector,
                embedding_model=settings.OPENAI_EMBEDDING_MODEL,
                chunk_index=index,
            )
        )
    doc.content = text
    doc.status = "ready"
    doc.chunk_count = len(pieces)
    doc.embedding_model = settings.OPENAI_EMBEDDING_MODEL
    doc.error_message = None
    doc.updated_at = _now()
    session.commit()
