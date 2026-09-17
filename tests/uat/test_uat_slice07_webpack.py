"""Slice 7 UAT: production webpack assets behind nginx."""

import re

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice07,
    pytest.mark.skipif(not slice_ready(7), reason=skip_reason(7)),
]


def test_hashed_assets_and_login_form(compose_stack: str) -> None:
    home = httpx.get(f"{compose_stack}/", timeout=10.0)
    assert home.status_code == 200
    assert "id=root" in home.text or 'id="root"' in home.text
    icon = httpx.get(f"{compose_stack}/ragged.png", timeout=5.0)
    assert icon.status_code == 200
    js = re.findall(r"/assets/[\w.-]+\.js", home.text)
    css = re.findall(r"/assets/[\w.-]+\.css", home.text)
    assert js
    assert css
    js_body = httpx.get(f"{compose_stack}{js[0]}", timeout=5.0)
    assert js_body.status_code == 200
    assert "auth/login" in js_body.text
    assert httpx.get(f"{compose_stack}{css[0]}", timeout=5.0).status_code == 200
