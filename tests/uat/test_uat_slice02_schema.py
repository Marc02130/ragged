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

    result = compose_support.compose(
        "exec",
        "-T",
        "db",
        "psql",
        "-U",
        "ragged",
        "-d",
        "ragged",
        "-c",
        r"\dx",
    )
    assert "vector" in result.stdout
    describe = compose_support.compose(
        "exec",
        "-T",
        "db",
        "psql",
        "-U",
        "ragged",
        "-d",
        "ragged",
        "-c",
        r"\d vector_chunks",
    )
    assert "1536" in describe.stdout
    assert "auth.users" not in describe.stdout
