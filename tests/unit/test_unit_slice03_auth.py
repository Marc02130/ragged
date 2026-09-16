"""Slice 3 unit: register/login/logout/me cookie JWT."""

from __future__ import annotations

import uuid
from datetime import timedelta

import bcrypt
import pytest

from tests.paths import AUTH_ROUTER
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice03,
    pytest.mark.skipif(not slice_ready(3), reason=skip_reason(3)),
]


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def test_auth_router_exists() -> None:
    text = AUTH_ROUTER.read_text()
    utils = (AUTH_ROUTER.parents[1] / "auth_utils.py").read_text()
    assert "register" in text
    assert "login" in text
    assert "logout" in text
    assert "httponly" in utils.lower()


def test_register_then_me(client) -> None:
    email = _email()
    registered = client.post(
        "/api/auth/register", json={"email": email, "password": "correct-horse"}
    )
    assert registered.status_code == 201
    body = registered.json()
    assert body["email"] == email
    assert "jwt" not in registered.text.lower()
    assert "access_token" not in body
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_login_cookie_flags(client) -> None:
    email = _email()
    client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    client.post("/api/auth/logout")
    login = client.post(
        "/api/auth/login", json={"email": email, "password": "correct-horse"}
    )
    assert login.status_code == 200
    cookie = login.headers.get("set-cookie", "")
    assert "ragged_session=" in cookie
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()
    assert "path=/" in cookie.lower()
    assert "domain=" not in cookie.lower()
    assert "jwt" not in login.text.lower()
    assert "access_token" not in login.json()


def test_logout_without_cookie_and_expired_cookie(client) -> None:
    bare = client.post("/api/auth/logout")
    assert bare.status_code == 204
    cookie = bare.headers.get("set-cookie", "")
    assert "ragged_session=" in cookie.lower() or "max-age=0" in cookie.lower()
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()
    assert "path=/" in cookie.lower()
    assert "domain=" not in cookie.lower()

    from app.auth_utils import encode_token
    from app.models import User

    email = _email()
    created = client.post(
        "/api/auth/register", json={"email": email, "password": "correct-horse"}
    )
    user = User(id=created.json()["id"], email=email, password_hash="x")
    expired = encode_token(user, expires_delta=timedelta(seconds=-10))
    client.cookies.set("ragged_session", expired)
    out = client.post("/api/auth/logout")
    assert out.status_code == 204
    assert "max-age=0" in out.headers.get("set-cookie", "").lower()


def test_duplicate_email_409(client) -> None:
    email = _email()
    client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    again = client.post(
        "/api/auth/register", json={"email": email.upper(), "password": "correct-horse"}
    )
    assert again.status_code == 409


def test_short_password_422(client) -> None:
    response = client.post(
        "/api/auth/register", json={"email": _email(), "password": "short"}
    )
    assert response.status_code == 422


def test_unknown_email_hits_dummy_bcrypt(client, monkeypatch) -> None:
    from app import auth_utils

    seen: list[bytes] = []
    real = bcrypt.checkpw

    def wrapped(password: bytes, hashed: bytes) -> bool:
        seen.append(hashed)
        return real(password, hashed)

    monkeypatch.setattr(auth_utils.bcrypt, "checkpw", wrapped)
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "correct-horse"},
    )
    assert response.status_code == 401
    assert seen
    assert seen[0] == auth_utils.DUMMY_HASH


def test_user_id_in_body_is_422(client) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": _email(),
            "password": "correct-horse",
            "user_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 422


def test_origin_allowlist_on_threads(client) -> None:
    email = _email()
    client.post("/api/auth/register", json={"email": email, "password": "correct-horse"})
    payload = {"title": "CSRF check"}
    ok_3000 = client.post(
        "/api/threads",
        json=payload,
        headers={"Origin": "http://localhost:3000"},
    )
    assert ok_3000.status_code == 200
    ok_8080 = client.post(
        "/api/threads",
        json=payload,
        headers={"Origin": "http://localhost:8080"},
    )
    assert ok_8080.status_code == 200
    evil = client.post(
        "/api/threads",
        json=payload,
        headers={"Origin": "http://evil.example"},
    )
    assert evil.status_code == 403


def test_cors_middleware_not_mounted() -> None:
    from app.main import app

    names = [getattr(m, "cls", type(m)).__name__ for m in app.user_middleware]
    assert "CORSMiddleware" not in names
