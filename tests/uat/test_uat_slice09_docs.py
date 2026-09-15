"""Slice 9 UAT: smoke script against a live key is skipped in CI without a key."""

import os

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice09,
    pytest.mark.skipif(not slice_ready(9), reason=skip_reason(9)),
]


def test_smoke_script_is_executable() -> None:
    if not os.environ.get("OPENAI_API_KEY", "").startswith("sk-"):
        pytest.skip("no live OPENAI_API_KEY")
    pytest.skip("run scripts/smoke.sh when slice 9 lands")
