"""Slice 3 UAT: register → me, cookie flags, Origin allowlist."""

import uuid

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
    email = f"uat-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=10.0) as client:
        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        assert response.status_code == 201
        cookie = response.headers.get("set-cookie", "")
        assert "ragged_session=" in cookie
        assert "httponly" in cookie.lower()
        assert "samesite=lax" in cookie.lower()
        assert "path=/" in cookie.lower()
        assert "domain=" not in cookie.lower()
        assert "access_token" not in response.json()
        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == email


def test_origin_allowlist_default_env(compose_stack: str) -> None:
    email = f"uat-origin-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=10.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        payload = {"title": "from browser"}
        assert (
            client.post(
                "/api/threads",
                json=payload,
                headers={"Origin": "http://localhost:3000"},
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/threads",
                json=payload,
                headers={"Origin": "http://localhost:8080"},
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/threads",
                json=payload,
                headers={"Origin": "http://evil.example"},
            ).status_code
            == 403
        )
