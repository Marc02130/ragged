"""Slice 9 UAT: smoke script is executable; live key is required to run it."""

import os
import stat

import pytest

from tests.paths import SMOKE
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice09,
    pytest.mark.skipif(not slice_ready(9), reason=skip_reason(9)),
]


def test_smoke_script_is_executable() -> None:
    mode = SMOKE.stat().st_mode
    assert mode & stat.S_IXUSR
    text = SMOKE.read_text()
    assert "placeholder" in text
    assert "sample.pdf" in text
    assert "OPENAI_API_KEY" in text
    assert "XAI_API_KEY" in text


def test_smoke_script_skipped_without_live_key() -> None:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key.startswith("sk-") or key.startswith("sk-replace") or key.startswith("sk-test"):
        pytest.skip("no live OPENAI_API_KEY")
    pytest.fail("live-key smoke is operator-run via scripts/smoke.sh")
