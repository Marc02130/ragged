"""Slice 2 UAT: pgvector extension and users FKs in the running DB."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice02,
    pytest.mark.skipif(not slice_ready(2), reason=skip_reason(2)),
]


def test_vector_extension_and_users_fk(compose_stack: str) -> None:
    from tests import compose_support

    dx = compose_support.psql(r"\dx")
    assert "vector" in dx

    chunks = compose_support.psql(r"\d vector_chunks")
    assert "384" in chunks
    assert "document_id" in chunks
    assert "auth.users" not in chunks

    documents = compose_support.psql(r"\d documents")
    assert "user_id" in documents
    assert "users" in documents
    assert "auth.users" not in documents

    users = compose_support.psql(r"\d users")
    assert "email" in users

    check = compose_support.psql(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conrelid = 'users'::regclass AND contype = 'c';"
    )
    assert "email = lower(email)" in check


def test_ready_selects_one(compose_stack: str) -> None:
    import httpx

    response = httpx.get(f"{compose_stack}/api/ready", timeout=5.0)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
