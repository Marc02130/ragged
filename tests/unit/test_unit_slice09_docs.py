"""Slice 9 unit: smoke script and README mention compose."""

import pytest

from tests.paths import ROOT, SMOKE
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice09,
    pytest.mark.skipif(not slice_ready(9), reason=skip_reason(9)),
]


def test_smoke_script_uses_live_openai_and_sample_pdf() -> None:
    text = SMOKE.read_text()
    assert "OPENAI_API_KEY" in text
    assert "XAI_API_KEY" in text
    assert "ANTHROPIC_API_KEY" in text
    assert "sample.pdf" in text
    assert "MiniLM" in text
    readme = (ROOT / "README.md").read_text()
    assert "docker compose up" in readme
    assert "PUBLIC_ORIGINS" in readme
    assert "all-MiniLM-L6-v2" in readme or "MiniLM" in readme
    assert "API keys" in readme
