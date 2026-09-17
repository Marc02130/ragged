"""Slice 7 dogfood: load the login page from nginx."""

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice07,
    pytest.mark.skipif(not slice_ready(7), reason=skip_reason(7)),
]


def test_operator_sees_login_form(compose_stack: str) -> None:
    home = httpx.get(f"{compose_stack}/", timeout=10.0)
    assert home.status_code == 200
    assert "id=root" in home.text or 'id="root"' in home.text
    icon = httpx.get(f"{compose_stack}/ragged.png", timeout=5.0)
    assert icon.status_code == 200
