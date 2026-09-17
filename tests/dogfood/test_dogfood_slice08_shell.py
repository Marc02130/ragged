"""Slice 8 dogfood: SPA shell plus API create-thread still works."""

import re
import uuid

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice08,
    pytest.mark.skipif(not slice_ready(8), reason=skip_reason(8)),
]


def test_operator_uses_the_spa(compose_stack: str) -> None:
    home = httpx.get(f"{compose_stack}/", timeout=10.0)
    assert home.status_code == 200
    js_names = re.findall(r"/assets/[\w.-]+\.js", home.text)
    bundle = httpx.get(f"{compose_stack}{js_names[0]}", timeout=10.0).text
    assert "Uploaded documents" in bundle
    assert "Ask a question about your documents" in bundle

    email = f"dogfood-shell-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=30.0) as client:
        assert (
            client.post(
                "/api/auth/register",
                json={"email": email, "password": "correct-horse-battery"},
            ).status_code
            == 201
        )
        created = client.post("/api/threads", json={"title": "from dogfood"})
        assert created.status_code == 201
        assert created.json()["title"] == "from dogfood"
