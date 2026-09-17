"""Slice 2 dogfood: inspect the DB the way an operator would."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice02,
    pytest.mark.skipif(not slice_ready(2), reason=skip_reason(2)),
]


def test_operator_can_describe_tables(compose_stack: str) -> None:
    from tests import compose_support

    users = compose_support.psql(r"\d users")
    assert "email" in users
    assert "password_hash" in users

    documents = compose_support.psql(r"\d documents")
    assert "thread_id" in documents
    assert "user_id" in documents

    chunks = compose_support.psql(r"\d vector_chunks")
    assert "embedding" in chunks
    assert "384" in chunks

    tables = compose_support.psql(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1;"
    )
    for name in ("users", "threads", "documents", "conversations", "vector_chunks"):
        assert name in tables
