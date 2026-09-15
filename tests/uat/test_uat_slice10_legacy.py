"""Slice 10 UAT: default compose has no Vite runtime."""

import pytest

from tests.paths import ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice10,
    pytest.mark.skipif(not slice_ready(10), reason=skip_reason(10)),
]


def test_grep_vite_clean_in_runtime_trees() -> None:
    for rel in ("web", "api", "docker-compose.yml"):
        path = ROOT / rel
        if path.is_file():
            assert "vite" not in path.read_text().lower()
