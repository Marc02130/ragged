"""Slice 4 unit: thread CRUD, archive, restore, delete."""

import pytest

from tests.paths import THREADS_ROUTER
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice04,
    pytest.mark.skipif(not slice_ready(4), reason=skip_reason(4)),
]


def test_threads_router_has_archive_restore_delete() -> None:
    text = THREADS_ROUTER.read_text()
    assert "archive" in text
    assert "restore" in text
    assert "delete" in text.lower()
