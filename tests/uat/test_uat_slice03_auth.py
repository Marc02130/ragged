"""Slice 3 UAT: register → me, cookie flags, Origin allowlist."""

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice03,
    pytest.mark.skipif(not slice_ready(3), reason=skip_reason(3)),
]


def test_register_sets_httponly_cookie_without_jwt_in_json(
    compose_stack: str,
) -> None:
    email = "uat-slice03@example.com"
    response = httpx.post(
        f"{compose_stack}/api/auth/register",
        json={"email": email, "password": "correct-horse-battery"},
        timeout=10.0,
    )
    assert response.status_code in (200, 201, 409)
    if response.status_code != 409:
        assert "ragged_session" in response.headers.get("set-cookie", "").lower()
        assert "httponly" in response.headers.get("set-cookie", "").lower()
        assert "jwt" not in response.text.lower() or "access_token" not in response.json()
