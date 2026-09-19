from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import User
from app.services import chat as chat_service
from app.services import embeddings as embeddings_service
from app.services import llm_keys

_JSON_OBJECT = re.compile(r"\{.*\}", re.S)

REWRITE_INSTRUCTIONS = """You expand a search query for a personal document RAG over papers, news, and notes.
Return JSON only, no markdown:
{"rewrite":"<one search query in the documents' own vocabulary>","aliases":["<up to 8 lay or jargon synonyms>"],"hyde":"<4-6 sentence hypothetical abstract or results paragraph that would answer the question>"}
Use earlier questions in the thread for topic. Do not answer the question. Do not cite sources."""

_EVIDENCE_ALIASES = (
    "hypothesize",
    "hypothesis",
    "we propose",
    "we found",
    "these findings",
    "these data suggest",
    "significantly",
)


@dataclass
class QueryPlan:
    rewrite: str = ""
    aliases: list[str] = field(default_factory=list)
    hyde: str = ""

    def embed_texts(self, original: str) -> list[str]:
        texts = [original]
        if self.rewrite and self.rewrite.strip() not in {original, texts[0]}:
            texts.append(self.rewrite.strip())
        if self.hyde.strip():
            texts.append(self.hyde.strip())
        return texts


def lexical_aliases(question: str) -> list[str]:
    """Paper-side stems when the user asked about evidence/hypotheses without those words."""
    q = (question or "").lower()
    if not any(k in q for k in ("hypothes", "evidence", "support", "mechanism", "finding", "strongest")):
        return []
    return list(_EVIDENCE_ALIASES)


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
    hyde = str(data.get("hyde") or "").strip()[:2000]
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
    return QueryPlan(rewrite=rewrite, aliases=aliases, hyde=hyde)


def build_rewrite_prompt(question: str, prior: list[str]) -> str:
    history = "\n".join(f"- {item}" for item in prior if item.strip()) or "(none)"
    return (
        f"{REWRITE_INSTRUCTIONS}\n\n"
        f"EARLIER QUESTIONS:\n{history}\n\n"
        f"CURRENT QUESTION:\n{question.strip()}"
    )


def rewrite_query(
    question: str,
    prior: list[str],
    user: User,
    session: Session,
) -> QueryPlan:
    fallback = QueryPlan(aliases=lexical_aliases(question))
    if embeddings_service.uses_stub_embeddings(user, session):
        return fallback
    llm = llm_keys.get_or_create_settings(session, user)
    if llm_keys.resolve_key(llm, llm.chat_provider) is None:
        return fallback
    try:
        raw = chat_service.complete(build_rewrite_prompt(question, prior), user, llm)
    except Exception:
        return fallback
    plan = parse_plan(raw)
    merged = list(dict.fromkeys([*plan.aliases, *fallback.aliases]))
    plan.aliases = merged[:8]
    if not plan.rewrite and not plan.hyde:
        plan.aliases = merged[:8]
    return plan
