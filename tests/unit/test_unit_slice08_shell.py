"""Slice 8 unit: App shell uses thread.id and api.ts envelope."""

import pytest

from tests.paths import WEB_APP, ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice08,
    pytest.mark.skipif(not slice_ready(8), reason=skip_reason(8)),
]


def test_app_passes_thread_id_not_thread_id_field() -> None:
    text = WEB_APP.read_text()
    assert "thread_id" not in text
    chat = (ROOT / "web" / "src" / "components" / "Chat" / "ChatInterface.tsx").read_text()
    assert "saveMessage" not in chat
    assert "assistant_message" in chat
    assert "data.response" not in chat
