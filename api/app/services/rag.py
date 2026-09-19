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
from app.services.chunk import expand_query, heading_boost, query_terms, unique_questions
from app.services.classify import excluded_roles, preferred_roles, resolve_role
from app.services.rewrite import QueryPlan, rewrite_query

RRF_K = 60
ROLE_BOOST = 0.05


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
        .limit(50)
    ).all()
    newest_first = [row for row in rows if row]
    return unique_questions(list(reversed(newest_first)), limit=8)


def _row_to_hit(row) -> Hit:
    role = resolve_role(row["content"], row["heading"] or "", row.get("role") or None)
    return Hit(
        chunk_id=row["id"],
        document_id=row["document_id"],
        file_name=row["file_name"],
        content=row["content"],
        chunk_index=row["chunk_index"],
        similarity=float(row["similarity"]),
        heading=row["heading"] or "",
        role=role,
    )


def _pool_score(hit: Hit, question: str, expanded: str, preferred: frozenset[str]) -> float:
    boost = heading_boost(hit.heading, question, expanded)
    role_bonus = ROLE_BOOST if hit.role in preferred else 0.0
    return hit.similarity + boost + role_bonus


def search_pool(
    session: Session,
    user_id: UUID,
    thread_id: UUID,
    query_vec: list[float],
    question: str,
    expanded: str,
    likes: list[str],
) -> list[Hit]:
    """Wide candidate rows. Citation/boilerplate dropped unless asked; other roles kept."""
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
    excluded = excluded_roles(question)
    preferred = preferred_roles(question)
    hits = [_row_to_hit(row) for row in rows]
    hits = [hit for hit in hits if hit.role not in excluded]
    hits.sort(key=lambda hit: _pool_score(hit, question, expanded, preferred), reverse=True)
    return hits


def search_chunks(
    session: Session,
    user_id: UUID,
    thread_id: UUID,
    query_vec: list[float],
    question: str,
    expanded: str,
) -> list[Hit]:
    likes = [f"%{term}%" for term in query_terms(question, expanded)]
    pool = search_pool(session, user_id, thread_id, query_vec, question, expanded, likes)
    return fuse_rrf([pool], question, expanded) if pool else []


def fuse_rrf(
    rankings: list[list[Hit]],
    question: str,
    expanded: str,
    k: int = RRF_K,
) -> list[Hit]:
    """Reciprocal rank fusion across original / rewrite / HyDE pools."""
    preferred = preferred_roles(question)
    scores: dict[UUID, float] = {}
    best: dict[UUID, Hit] = {}
    for ranking in rankings:
        if not ranking:
            continue
        ordered = sorted(
            ranking,
            key=lambda hit: _pool_score(hit, question, expanded, preferred),
            reverse=True,
        )
        for rank, hit in enumerate(ordered):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            prev = best.get(hit.chunk_id)
            if prev is None or hit.similarity > prev.similarity:
                best[hit.chunk_id] = hit
    scored = [(score, best[cid]) for cid, score in scores.items()]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [hit for _score, hit in scored[: settings.MAX_VECTOR_RESULTS]]


def nearest_chunks(
    session: Session,
    user_id: UUID,
    thread_id: UUID,
    query_vec: list[float],
    question: str,
) -> list[Hit]:
    """Top-k by cosine with no cutoff. Used when the wide pool is empty
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
    excluded = excluded_roles(question)
    preferred = preferred_roles(question)
    parsed = [_row_to_hit(row) for row in rows]
    hits = [hit for hit in parsed if hit.role not in excluded]
    hits.sort(key=lambda hit: _pool_score(hit, question, "", preferred), reverse=True)
    return hits[: settings.MAX_VECTOR_RESULTS]


def complete(prompt: str, user: User, session: Session) -> str:
    llm = llm_keys.get_or_create_settings(session, user)
    if llm_keys.resolve_key(llm, llm.chat_provider) is None:
        return "Answer based on SOURCES."
    try:
        return chat_service.complete(prompt, user, llm)
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def retrieve_hits(
    session: Session,
    user: User,
    thread_id: UUID,
    question: str,
    prior: list[str],
    plan: QueryPlan,
) -> list[Hit]:
    user_id = user.id
    expanded = expand_query(question, prior)
    texts = plan.embed_texts(expanded)
    vectors = embeddings_service.embed_texts(texts, user=user, session=session)
    if not vectors:
        return []
    likes = [
        f"%{term}%"
        for term in query_terms(
            question,
            expanded,
            plan.rewrite,
            *plan.aliases,
            limit=16,
        )
    ]
    rankings = [
        search_pool(session, user_id, thread_id, vec, question, expanded, likes)
        for vec in vectors
    ]
    hits = fuse_rrf(rankings, question, expanded)
    if hits:
        return hits
    return nearest_chunks(session, user_id, thread_id, vectors[0], question)


def answer(
    session: Session, user: User, thread_id: UUID, question: str
) -> tuple[Conversation, Conversation]:
    prior = _prior_user_questions(session, thread_id, user.id)
    plan = rewrite_query(question, prior, user, session)
    hits = retrieve_hits(session, user, thread_id, question, prior, plan)
    user_row = Conversation(
        thread_id=thread_id,
        user_id=user.id,
        role="user",
        content=question,
        extra={"sources": []},
    )
    session.add(user_row)
    if not hits:
        assistant_row = Conversation(
            thread_id=thread_id,
            user_id=user.id,
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
    stored_sources = [] if content.strip() == CANNED_REFUSAL else sources
    assistant_row = Conversation(
        thread_id=thread_id,
        user_id=user.id,
        role="assistant",
        content=content,
        extra={"sources": stored_sources},
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
