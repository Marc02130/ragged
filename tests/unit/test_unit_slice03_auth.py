"""Slice 3 unit: register/login/logout/me cookie JWT."""

import pytest

from tests.paths import AUTH_ROUTER
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice03,
    pytest.mark.skipif(not slice_ready(3), reason=skip_reason(3)),
]


def test_auth_router_exists() -> None:
    text = AUTH_ROUTER.read_text()
    assert "register" in text
    assert "login" in text
    assert "logout" in text
    assert "httponly" in text.lower() or "HttpOnly" in text or "httponly=True" in text
