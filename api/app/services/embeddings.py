from __future__ import annotations

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
    return _client


def uses_stub_embeddings() -> bool:
    key = settings.OPENAI_API_KEY
    return (
        key.startswith("sk-replace")
        or key.startswith("sk-test")
        or key == "sk-not-set"
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if uses_stub_embeddings():
        return [[0.01] * settings.EMBEDDING_DIM for _ in texts]
    client = get_client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), 50):
        batch = texts[start : start + 50]
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=batch,
        )
        vectors.extend(item.embedding for item in response.data)
    return vectors
