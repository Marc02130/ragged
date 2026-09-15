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
