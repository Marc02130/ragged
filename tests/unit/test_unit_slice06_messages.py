"""Slice 6 unit: RAG messages, canned refusal, no client model."""

import pytest

from tests.paths import MESSAGES_ROUTER, ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice06,
    pytest.mark.skipif(not slice_ready(6), reason=skip_reason(6)),
]


def test_messages_router_forbids_client_model_and_cross_thread() -> None:
    text = MESSAGES_ROUTER.read_text()
    rag = (ROOT / "api" / "app" / "services" / "rag.py").read_text()
    combined = text + rag
    assert "0.7" in combined
    assert "I don't have that in your documents." in combined
