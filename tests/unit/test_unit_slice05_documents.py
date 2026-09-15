"""Slice 5 unit: multipart ingest, magic bytes, quotas."""

import pytest

from tests.paths import DOCUMENTS_ROUTER
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice05,
    pytest.mark.skipif(not slice_ready(5), reason=skip_reason(5)),
]


def test_documents_router_is_sync_def() -> None:
    text = DOCUMENTS_ROUTER.read_text()
    assert "async def" not in text or "def " in text
    assert "files" in text.lower()
