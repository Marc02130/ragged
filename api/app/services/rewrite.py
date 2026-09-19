from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Document, Thread, User
from app.services import chat as chat_service
from app.services import embeddings as embeddings_service
from app.services import llm_keys

_JSON_OBJECT = re.compile(r"\{.*\}", re.S)

REWRITE_INSTRUCTIONS = """You expand a search query for a personal RAG over mixed documents (papers, news, letters, notes).
Use THREAD TITLE, FILES, and HEADINGS as the corpus.
Write rewrite as a standalone question in these documents' own vocabulary — not a scientific abstract.
Aliases are people, places, dates, nicknames, and other names a reader would type.
hyde is two short hypothetical passages in different registers: [0] a news lede, [1] a plain personal note. Not an academic abstract.
Return JSON only, no markdown:
{"rewrite":"<standalone question>","aliases":["<name or nickname>"],"hyde":["<news lede>","<plain note>"]}
Do not answer the question. Do not cite sources."""


@dataclass
class ThreadCorpus:
    title: str = ""
    files: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)

    def prompt_block(self) -> str:
        files = ", ".join(self.files[:20]) or "(none)"
        heads = "; ".join(h for h in self.headings[:40] if h) or "(none)"
        return (
            f"THREAD TITLE: {self.title or '(none)'}\n"
            f"FILES: {files}\n"
            f"HEADINGS: {heads}"
        )


@dataclass
class QueryPlan:
    rewrite: str = ""
    aliases: list[str] = field(default_factory=list)
    hyde: list[str] = field(default_factory=list)

    def embed_texts(self, original: str = "") -> list[str]:
        texts: list[str] = []
        seen: set[str] = set()

        def add(value: str) -> None:
            token = (value or "").strip()
            if not token or token in seen:
                return
            seen.add(token)
            texts.append(token)

        add(original)
        add(self.rewrite)
        for passage in self.hyde:
            add(passage)
        return texts


def load_thread_corpus(session: Session, thread_id: UUID | None) -> ThreadCorpus:
    if thread_id is None:
        return ThreadCorpus()
    thread = session.get(Thread, thread_id)
    files = list(
        session.scalars(
            select(Document.file_name)
            .where(Document.thread_id == thread_id, Document.status == "ready")
            .order_by(Document.created_at)
            .limit(20)
        ).all()
    )
    heading_rows = session.execute(
        text(
            """
            SELECT DISTINCT metadata->>'heading' AS heading
            FROM vector_chunks
            WHERE thread_id = :tid
              AND coalesce(metadata->>'heading', '') <> ''
            LIMIT 40
            """
        ),
        {"tid": thread_id},
    )
    headings = [row[0] for row in heading_rows if row[0]]
    return ThreadCorpus(
        title=(thread.title if thread is not None else "") or "",
        files=files,
        headings=headings,
    )


def parse_plan(raw: str) -> QueryPlan:
    blob = (raw or "").strip()
    if not blob:
        return QueryPlan()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", blob, re.S)
    if fenced:
        blob = fenced.group(1)
    match = _JSON_OBJECT.search(blob)
    if not match:
        return QueryPlan()
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return QueryPlan()
    if not isinstance(data, dict):
        return QueryPlan()
    rewrite = str(data.get("rewrite") or "").strip()[:500]
    aliases: list[str] = []
    seen: set[str] = set()
    raw_aliases = data.get("aliases") or []
    if isinstance(raw_aliases, str):
        raw_aliases = [raw_aliases]
    if isinstance(raw_aliases, list):
        for item in raw_aliases:
            token = str(item).strip()[:80]
            key = token.lower()
            if len(token) < 3 or key in seen:
                continue
            seen.add(key)
            aliases.append(token)
            if len(aliases) >= 8:
                break
    passages: list[str] = []
    hyde = data.get("hyde")
    if isinstance(hyde, str) and hyde.strip():
        passages.append(hyde.strip()[:800])
    elif isinstance(hyde, list):
        for item in hyde:
            token = str(item).strip()[:800]
            if token:
                passages.append(token)
            if len(passages) >= 2:
                break
    for key in ("lede", "news", "note"):
        extra = str(data.get(key) or "").strip()[:800]
        if extra and extra not in passages and len(passages) < 2:
            passages.append(extra)
    return QueryPlan(rewrite=rewrite, aliases=aliases, hyde=passages[:2])


def build_rewrite_prompt(
    question: str,
    prior: list[str],
    corpus: ThreadCorpus | None = None,
) -> str:
    history = "\n".join(f"- {item}" for item in prior if item.strip()) or "(none)"
    block = (corpus or ThreadCorpus()).prompt_block()
    return (
        f"{REWRITE_INSTRUCTIONS}\n\n"
        f"{block}\n\n"
        f"EARLIER QUESTIONS:\n{history}\n\n"
        f"CURRENT QUESTION:\n{question.strip()}"
    )


def rewrite_query(
    question: str,
    prior: list[str],
    user: User,
    session: Session,
    thread_id: UUID | None = None,
) -> QueryPlan:
    empty = QueryPlan()
    if embeddings_service.uses_stub_embeddings(user, session):
        return empty
    llm = llm_keys.get_or_create_settings(session, user)
    if llm_keys.resolve_key(llm, llm.chat_provider) is None:
        return empty
    corpus = load_thread_corpus(session, thread_id)
    try:
        raw = chat_service.complete(
            build_rewrite_prompt(question, prior, corpus), user, llm
        )
    except Exception:
        return empty
    return parse_plan(raw)
