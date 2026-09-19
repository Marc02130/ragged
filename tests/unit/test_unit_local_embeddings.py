"""Local MiniLM embeddings: 384-d, stub in tests, no OpenAI for ingest."""

from __future__ import annotations

import pytest

from tests.paths import ROOT

pytestmark = [pytest.mark.unit]


def test_config_is_local_minilm_384() -> None:
    from app.config import settings

    assert settings.EMBEDDING_DIM == 384
    assert "MiniLM" in settings.EMBEDDING_MODEL
    assert settings.EMBEDDING_PROVIDER == "stub"


def test_migration_0003_uses_vector_384() -> None:
    text = (ROOT / "api" / "alembic" / "versions" / "0003_local_embeddings.py").read_text()
    assert "vector(384)" in text
    assert "1536" in text  # downgrade only


def test_stub_embed_texts_is_384() -> None:
    from app.services.embeddings import embed_texts, uses_stub_embeddings

    assert uses_stub_embeddings() is True
    vectors = embed_texts(["hello ragged"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 384


def test_stub_embed_texts_returns_one_vector_per_input() -> None:
    from app.services.embeddings import EMBED_BATCH, embed_texts

    assert EMBED_BATCH == 32
    vectors = embed_texts(["chunk"] * 40)
    assert len(vectors) == 40
    assert all(len(vec) == 384 for vec in vectors)
