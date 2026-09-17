from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from datetime import datetime, timezone

from fastapi import HTTPException
from app.models import Conversation, Thread, User
from app.prompts import CANNED_REFUSAL, build_prompt
from app.services import chat as chat_service
from app.services import embeddings as embeddings_service
from app.services import llm_keys


@dataclass
class Hit:
    chunk_id: UUID
    document_id: UUID
    file_name: str
    content: str
    chunk_index: int
    similarity: float

    def as_source(self) -> dict:
        return {
            "chunk_id": str(self.chunk_id),
            "document_id": str(self.document_id),
            "file_name": self.file_name,
            "content": self.content,
            "similarity": self.similarity,
            "chunk_index": self.chunk_index,
        }


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def search_chunks(
    session: Session, user_id: UUID, thread_id: UUID, query_vec: list[float]
) -> list[Hit]:
    sql = text(
        """
        SELECT
          vc.id,
          vc.document_id,
          vc.content,
          vc.chunk_index,
          d.file_name,
          1 - (vc.embedding <=> CAST(:qvec AS vector)) AS similarity
        FROM vector_chunks vc
        JOIN documents d ON d.id = vc.document_id
        WHERE vc.user_id = :user_id
          AND vc.thread_id = :thread_id
          AND vc.embedding_model = :model
          AND 1 - (vc.embedding <=> CAST(:qvec AS vector)) >= :threshold
        ORDER BY vc.embedding <=> CAST(:qvec AS vector)
        LIMIT :k
        """
    )
    rows = session.execute(
        sql,
        {
            "qvec": _vector_literal(query_vec),
            "user_id": user_id,
            "thread_id": thread_id,
            "model": settings.EMBEDDING_MODEL,
            "threshold": settings.SIMILARITY_THRESHOLD,
            "k": settings.MAX_VECTOR_RESULTS,
        },
    ).mappings()
    return [
        Hit(
            chunk_id=row["id"],
            document_id=row["document_id"],
            file_name=row["file_name"],
            content=row["content"],
            chunk_index=row["chunk_index"],
            similarity=float(row["similarity"]),
        )
        for row in rows
    ]


def complete(prompt: str, user: User, session: Session) -> str:
    llm = llm_keys.get_or_create_settings(session, user)
    if llm_keys.resolve_key(llm, llm.chat_provider) is None:
        return "Answer based on SOURCES."
    try:
        return chat_service.complete(prompt, user, llm)
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def answer(
    session: Session, user: User, thread_id: UUID, question: str
) -> tuple[Conversation, Conversation]:
    user_id = user.id
    query_vec = embeddings_service.embed_texts([question], user=user, session=session)[0]
    hits = search_chunks(session, user_id, thread_id, query_vec)
    user_row = Conversation(
        thread_id=thread_id,
        user_id=user_id,
        role="user",
        content=question,
        extra={"sources": []},
    )
    session.add(user_row)
    if not hits:
        assistant_row = Conversation(
            thread_id=thread_id,
            user_id=user_id,
            role="assistant",
            content=CANNED_REFUSAL,
            extra={"sources": []},
        )
        session.add(assistant_row)
        _touch_thread(session, thread_id)
        session.commit()
        session.refresh(user_row)
        session.refresh(assistant_row)
        return user_row, assistant_row

    sources = [hit.as_source() for hit in hits]
    prompt = build_prompt(question, sources)
    content = complete(prompt, user, session)
    assistant_row = Conversation(
        thread_id=thread_id,
        user_id=user_id,
        role="assistant",
        content=content,
        extra={"sources": sources},
    )
    session.add(assistant_row)
    _touch_thread(session, thread_id)
    session.commit()
    session.refresh(user_row)
    session.refresh(assistant_row)
    return user_row, assistant_row


def _touch_thread(session: Session, thread_id: UUID) -> None:
    thread = session.get(Thread, thread_id)
    if thread is not None:
        thread.last_activity_at = datetime.now(timezone.utc)
        thread.updated_at = datetime.now(timezone.utc)
