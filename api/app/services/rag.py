from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import String, bindparam, select, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Conversation, Thread, User
from app.prompts import CANNED_REFUSAL, build_prompt
from app.services import chat as chat_service
from app.services import embeddings as embeddings_service
from app.services import llm_keys
from app.services.chunk import expand_query, heading_boost, query_terms
from app.services.classify import allowed_roles, resolve_role


@dataclass
class Hit:
    chunk_id: UUID
    document_id: UUID
    file_name: str
    content: str
    chunk_index: int
    similarity: float
    heading: str = ""
    role: str = ""

    def as_source(self) -> dict:
        return {
            "chunk_id": str(self.chunk_id),
            "document_id": str(self.document_id),
            "file_name": self.file_name,
            "content": self.content,
            "similarity": self.similarity,
            "chunk_index": self.chunk_index,
            "heading": self.heading,
            "role": self.role,
        }


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def _candidate_threshold() -> float:
    return max(0.2, settings.SIMILARITY_THRESHOLD - 0.2)


def _prior_user_questions(session: Session, thread_id: UUID, user_id: UUID) -> list[str]:
    rows = session.scalars(
        select(Conversation.content)
        .where(
            Conversation.thread_id == thread_id,
            Conversation.user_id == user_id,
            Conversation.role == "user",
        )
        .order_by(Conversation.created_at.desc())
        .limit(2)
    ).all()
    return list(reversed(list(rows)))


def search_chunks(
    session: Session,
    user_id: UUID,
    thread_id: UUID,
    query_vec: list[float],
    question: str,
    expanded: str,
) -> list[Hit]:
    likes = [f"%{term}%" for term in query_terms(question, expanded)]
    candidate = _candidate_threshold()
    wide_k = max(24, settings.MAX_VECTOR_RESULTS * 3)
    sql = text(
        """
        SELECT
          vc.id,
          vc.document_id,
          vc.content,
          vc.chunk_index,
          d.file_name,
          COALESCE(vc.metadata->>'heading', '') AS heading,
          COALESCE(vc.metadata->>'role', '') AS role,
          1 - (vc.embedding <=> CAST(:qvec AS vector)) AS similarity
        FROM vector_chunks vc
        JOIN documents d ON d.id = vc.document_id
        WHERE vc.user_id = :user_id
          AND vc.thread_id = :thread_id
          AND vc.embedding_model = :model
          AND (
            1 - (vc.embedding <=> CAST(:qvec AS vector)) >= :candidate
            OR (
              :has_likes
              AND (
                vc.content ILIKE ANY(:likes)
                OR COALESCE(vc.metadata->>'heading', '') ILIKE ANY(:likes)
              )
            )
          )
        ORDER BY vc.embedding <=> CAST(:qvec AS vector)
        LIMIT :wide_k
        """
    ).bindparams(bindparam("likes", type_=ARRAY(String)))
    rows = session.execute(
        sql,
        {
            "qvec": _vector_literal(query_vec),
            "user_id": user_id,
            "thread_id": thread_id,
            "model": settings.EMBEDDING_MODEL,
            "candidate": candidate,
            "has_likes": bool(likes),
            "likes": likes or ["__no_lexical_match__"],
            "wide_k": wide_k,
        },
    ).mappings()
    allowed = allowed_roles(question)
    scored: list[tuple[float, Hit]] = []
    for row in rows:
        role = resolve_role(row["content"], row["heading"] or "", row.get("role") or None)
        if role not in allowed:
            continue
        hit = Hit(
            chunk_id=row["id"],
            document_id=row["document_id"],
            file_name=row["file_name"],
            content=row["content"],
            chunk_index=row["chunk_index"],
            similarity=float(row["similarity"]),
            heading=row["heading"] or "",
            role=role,
        )
        boost = heading_boost(hit.heading, question, expanded)
        score = hit.similarity + boost
        keep = score >= settings.SIMILARITY_THRESHOLD or (
            boost >= 0.12 and hit.similarity >= candidate
        )
        if keep:
            scored.append((score, hit))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [hit for _score, hit in scored[: settings.MAX_VECTOR_RESULTS]]


def nearest_chunks(
    session: Session,
    user_id: UUID,
    thread_id: UUID,
    query_vec: list[float],
    question: str,
) -> list[Hit]:
    """Top-k by cosine with no cutoff. Used when the threshold screen is empty
    but the thread already has papers (follow-ups, 'review the documents', etc.)."""
    sql = text(
        """
        SELECT
          vc.id,
          vc.document_id,
          vc.content,
          vc.chunk_index,
          d.file_name,
          COALESCE(vc.metadata->>'heading', '') AS heading,
          COALESCE(vc.metadata->>'role', '') AS role,
          1 - (vc.embedding <=> CAST(:qvec AS vector)) AS similarity
        FROM vector_chunks vc
        JOIN documents d ON d.id = vc.document_id
        WHERE vc.user_id = :user_id
          AND vc.thread_id = :thread_id
          AND vc.embedding_model = :model
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
            "k": max(32, settings.MAX_VECTOR_RESULTS * 4),
        },
    ).mappings()
    allowed = allowed_roles(question)
    parsed: list[Hit] = []
    for row in rows:
        role = resolve_role(row["content"], row["heading"] or "", row.get("role") or None)
        parsed.append(
            Hit(
                chunk_id=row["id"],
                document_id=row["document_id"],
                file_name=row["file_name"],
                content=row["content"],
                chunk_index=row["chunk_index"],
                similarity=float(row["similarity"]),
                heading=row["heading"] or "",
                role=role,
            )
        )
    hits = [h for h in parsed if h.role in allowed]
    if not hits:
        from app.services.classify import DEFAULT_RETRIEVE

        hits = [h for h in parsed if h.role in DEFAULT_RETRIEVE]
    return hits[: settings.MAX_VECTOR_RESULTS]


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
    prior = _prior_user_questions(session, thread_id, user_id)
    expanded = expand_query(question, prior)
    query_vec = embeddings_service.embed_texts([expanded], user=user, session=session)[0]
    hits = search_chunks(session, user_id, thread_id, query_vec, question, expanded)
    if not hits:
        hits = nearest_chunks(session, user_id, thread_id, query_vec, question)
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
