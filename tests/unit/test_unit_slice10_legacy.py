"""Slice 10 unit: Vite/Supabase runtime trees are gone."""

import pytest

from tests.paths import ROOT, VITE_CONFIG
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice10,
    pytest.mark.skipif(not slice_ready(10), reason=skip_reason(10)),
]


def test_vite_and_supabase_runtime_removed() -> None:
    assert not VITE_CONFIG.exists()
    assert not (ROOT / "src" / "App.tsx").exists()
    assert not (ROOT / "supabase" / "functions").exists()
    assert not (ROOT / "example-code").exists()
