"""Slice 2 unit: Alembic initial schema."""

import pytest

from tests.paths import ALEMBIC_INITIAL
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice02,
    pytest.mark.skipif(not slice_ready(2), reason=skip_reason(2)),
]


def test_initial_migration_uses_pgvector_1536_and_users_table() -> None:
    text = ALEMBIC_INITIAL.read_text()
    assert "vector(1536)" in text or "VECTOR(1536)" in text
    assert "auth.users" not in text
    assert "email = lower(email)" in text
    assert "uuid-ossp" not in text
    assert "hnsw" in text.lower() or "HNSW" in text
    assert "REFERENCES users(id)" in text
    assert "idx_documents_user" in text
    assert "idx_chunks_document_id" in text
    assert "CREATE EXTENSION IF NOT EXISTS vector" in text


def test_alembic_applies_vector_extension(postgres_url: str) -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        names = [
            row[0]
            for row in conn.execute(text("SELECT extname FROM pg_extension")).fetchall()
        ]
    assert "vector" in names
    assert "uuid-ossp" not in names


def test_alembic_vector_chunks_and_fks(postgres_url: str) -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        dim = conn.execute(
            text(
                """
                SELECT format_type(a.atttypid, a.atttypmod)
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                WHERE c.relname = 'vector_chunks'
                  AND a.attname = 'embedding'
                  AND a.attnum > 0
                """
            )
        ).scalar_one()
        assert dim == "vector(1536)"
        fks = conn.execute(
            text(
                """
                SELECT conrelid::regclass::text, confrelid::regclass::text
                FROM pg_constraint
                WHERE contype = 'f'
                  AND conrelid::regclass::text IN
                    ('documents', 'vector_chunks', 'threads', 'conversations')
                """
            )
        ).fetchall()
    refs = {row[1] for row in fks}
    assert "users" in refs
    assert "auth.users" not in refs


def test_alembic_users_email_check(postgres_url: str) -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        check = conn.execute(
            text(
                """
                SELECT pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'users'::regclass AND contype = 'c'
                """
            )
        ).scalar_one()
    assert "email = lower(email)" in check
