"""Slice 8 UAT: thread sidebar, upload, chat in the production bundle."""

import re

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice08,
    pytest.mark.skipif(not slice_ready(8), reason=skip_reason(8)),
]


def test_spa_shell_loads(compose_stack: str) -> None:
    home = httpx.get(f"{compose_stack}/", timeout=10.0)
    assert home.status_code == 200
    js_names = re.findall(r"/assets/[\w.-]+\.js", home.text)
    assert js_names
    js = httpx.get(f"{compose_stack}{js_names[0]}", timeout=10.0)
    assert js.status_code == 200
    text = js.text
    assert "Create New Thread" in text
    assert "assistant_message" in text
    assert "saveMessage" not in text
    assert "exceeds 10MB limit" in text
