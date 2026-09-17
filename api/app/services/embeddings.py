from __future__ import annotations

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.services import llm_keys

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
    return _client


def uses_stub_embeddings(user: User | None = None, session: Session | None = None) -> bool:
    key = _embedding_key(user, session)
    return key is None


def _embedding_key(user: User | None, session: Session | None) -> str | None:
    row = None
    if user is not None and session is not None:
        row = llm_keys.get_or_create_settings(session, user)
    return llm_keys.resolve_key(row, "openai")


def embed_texts(
    texts: list[str],
    user: User | None = None,
    session: Session | None = None,
) -> list[list[float]]:
    if not texts:
        return []
    key = _embedding_key(user, session)
    if key is None:
        return [[0.01] * settings.EMBEDDING_DIM for _ in texts]
    client = OpenAI(api_key=key, timeout=settings.OPENAI_TIMEOUT_SECONDS)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), 50):
        batch = texts[start : start + 50]
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=batch,
        )
        vectors.extend(item.embedding for item in response.data)
    return vectors
