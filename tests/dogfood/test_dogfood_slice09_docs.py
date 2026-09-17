"""Slice 9 dogfood: README documents compose, origins, TLS, backups."""

import pytest

from tests.paths import ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice09,
    pytest.mark.skipif(not slice_ready(9), reason=skip_reason(9)),
]


def test_operator_follows_readme(compose_stack: str) -> None:
    readme = (ROOT / "README.md").read_text()
    assert "docker compose up" in readme
    assert "PUBLIC_ORIGINS" in readme
    assert "COOKIE_SECURE" in readme
    assert "pg_dump" in readme
    assert "pgdata" in readme
    assert "uploads" in readme
    assert "docker compose down" in readme
    assert "docker compose down -v" in readme
    assert "MiniLM" in readme or "local" in readme.lower()
    assert compose_stack.startswith("http://")
