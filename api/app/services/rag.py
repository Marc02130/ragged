from __future__ import annotations

import json
import re
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
_KEEP_JSON = re.compile(r"\{.*\}", re.S)
GRADE_INSTRUCTIONS = """Filter retrieved chunks for a personal RAG app.
Return JSON only: {"keep": [1, 3]} using the chunk numbers.
Keep chunks that contain a hypothesis, finding, mechanism, or evidence that helps answer the question.
Drop bibliography, numbered reference lists, paper titles with no body, and author lists."""


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


def _wide_k() -> int:
    return max(settings.WIDE_VECTOR_RESULTS, settings.MAX_VECTOR_RESULTS * 4)


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


def nearest_chunks(
    session: Session,
    user_id: UUID,
    thread_id: UUID,
    query_vec: list[float],
    question: str,
    expanded: str = "",
    likes: list[str] | None = None,
) -> list[Hit]:
    """Wide nearest-N with no cosine cliff. Default retrieval pool."""
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
            "k": _wide_k(),
        },
    ).mappings()
    excluded = excluded_roles(question)
    preferred = preferred_roles(question)
    by_id: dict[UUID, Hit] = {}
    for row in rows:
        hit = _row_to_hit(row)
        if hit.role in excluded:
            continue
        by_id[hit.chunk_id] = hit
    if likes:
        lex_sql = text(
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
                vc.content ILIKE ANY(:likes)
                OR COALESCE(vc.metadata->>'heading', '') ILIKE ANY(:likes)
              )
            LIMIT :k
            """
        ).bindparams(bindparam("likes", type_=ARRAY(String)))
        lex_rows = session.execute(
            lex_sql,
            {
                "qvec": _vector_literal(query_vec),
                "user_id": user_id,
                "thread_id": thread_id,
                "model": settings.EMBEDDING_MODEL,
                "likes": likes,
                "k": _wide_k(),
            },
        ).mappings()
        for row in lex_rows:
            hit = _row_to_hit(row)
            if hit.role in excluded:
                continue
            prev = by_id.get(hit.chunk_id)
            if prev is None or hit.similarity > prev.similarity:
                by_id[hit.chunk_id] = hit
    hits = list(by_id.values())
    hits.sort(key=lambda hit: _pool_score(hit, question, expanded, preferred), reverse=True)
    return hits


def search_pool(
    session: Session,
    user_id: UUID,
    thread_id: UUID,
    query_vec: list[float],
    question: str,
    expanded: str,
    likes: list[str],
) -> list[Hit]:
    return nearest_chunks(
        session, user_id, thread_id, query_vec, question, expanded, likes or None
    )


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
    return relative_cut(fuse_rrf([pool], question, expanded)) if pool else []


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
    return [hit for _score, hit in scored]


def relative_cut(hits: list[Hit]) -> list[Hit]:
    """Keep hits within RELATIVE_SCORE_MARGIN of the best cosine. Not a 0.4 cliff."""
    if not hits:
        return []
    best = max(hit.similarity for hit in hits)
    floor = best - settings.RELATIVE_SCORE_MARGIN
    kept = [hit for hit in hits if hit.similarity >= floor]
    return kept[: settings.MAX_VECTOR_RESULTS]


def _parse_keep(raw: str, n: int) -> list[int]:
    match = _KEEP_JSON.search(raw or "")
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    keep = data.get("keep") if isinstance(data, dict) else None
    if not isinstance(keep, list):
        return []
    out: list[int] = []
    for item in keep:
        try:
            idx = int(item)
        except (TypeError, ValueError):
            continue
        if 1 <= idx <= n and idx not in out:
            out.append(idx)
    return out


def expand_neighbors(
    session: Session,
    hits: list[Hit],
    question: str,
) -> list[Hit]:
    """If a hit is a title fragment, pull the adjacent chunk from the same file."""
    excluded = excluded_roles(question)
    seen = {hit.chunk_id for hit in hits}
    extra: list[Hit] = []
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
          :sim AS similarity
        FROM vector_chunks vc
        JOIN documents d ON d.id = vc.document_id
        WHERE vc.document_id = :doc
          AND vc.chunk_index = :idx
        LIMIT 1
        """
    )
    for hit in hits:
        if len(hit.content.strip()) >= 160:
            continue
        for neighbor_index in (hit.chunk_index - 1, hit.chunk_index + 1):
            if neighbor_index < 0:
                continue
            row = session.execute(
                sql,
                {"sim": hit.similarity, "doc": hit.document_id, "idx": neighbor_index},
            ).mappings().first()
            if row is None:
                continue
            neighbor = _row_to_hit(row)
            if neighbor.chunk_id in seen or neighbor.role in excluded:
                continue
            seen.add(neighbor.chunk_id)
            extra.append(neighbor)
    return hits + extra


def grade_hits(
    hits: list[Hit],
    question: str,
    user: User,
    session: Session,
) -> list[Hit]:
    """Drop bibliography/titles the retriever still ranked high. One cheap chat call."""
    if len(hits) <= 1 or embeddings_service.uses_stub_embeddings(user, session):
        return hits
    llm = llm_keys.get_or_create_settings(session, user)
    if llm_keys.resolve_key(llm, llm.chat_provider) is None:
        return hits
    lines = []
    for index, hit in enumerate(hits, start=1):
        snippet = hit.content.replace("\n", " ").strip()[:400]
        lines.append(f"[{index}] {snippet}")
    prompt = (
        f"{GRADE_INSTRUCTIONS}\n\nQUESTION:\n{question}\n\nCHUNKS:\n" + "\n".join(lines)
    )
    try:
        raw = chat_service.complete(prompt, user, llm)
    except Exception:
        return hits
    keep = _parse_keep(raw, len(hits))
    if not keep:
        return hits
    return [hits[index - 1] for index in keep]


def retrieve_hits(
    session: Session,
    user: User,
    thread_id: UUID,
    question: str,
    prior: list[str],
    plan: QueryPlan,
    *,
    include_original: bool = True,
) -> list[Hit]:
    user_id = user.id
    expanded = expand_query(question, prior) if include_original else ""
    original = expanded if include_original else ""
    texts = plan.embed_texts(original)
    if not texts:
        return []
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
        nearest_chunks(
            session, user_id, thread_id, vec, question, expanded, likes or None
        )
        for vec in vectors
    ]
    fused = fuse_rrf(rankings, question, expanded)
    hits = relative_cut(fused)
    hits = expand_neighbors(session, hits, question)
    hits = grade_hits(hits, question, user, session)
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
    prior = _prior_user_questions(session, thread_id, user.id)
    plan = rewrite_query(question, prior, user, session, thread_id=thread_id)
    hits = retrieve_hits(session, user, thread_id, question, prior, plan)
    if not hits:
        hits = retrieve_hits(
            session,
            user,
            thread_id,
            question,
            prior,
            plan,
            include_original=False,
        )
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
