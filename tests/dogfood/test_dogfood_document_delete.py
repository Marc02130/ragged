"""Dogfood: Delete is in the SPA bundle; API delete works."""

import re
import uuid

import httpx
import pytest

from tests.paths import ROOT

pytestmark = [pytest.mark.dogfood]

SAMPLE_PDF = ROOT / "api" / "tests" / "fixtures" / "sample.pdf"


def test_operator_can_delete_a_document(compose_stack: str) -> None:
    home = httpx.get(f"{compose_stack}/", timeout=10.0)
    js_names = re.findall(r"/assets/[\w.-]+\.js", home.text)
    bundle = httpx.get(f"{compose_stack}{js_names[0]}", timeout=10.0).text
    assert "Delete document" in bundle or "Remove" in bundle

    email = f"dogfood-del-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=120.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "del"}).json()["id"]
        uploaded = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("sample.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
        )
        doc_id = uploaded.json()[0]["id"]
        assert client.delete(f"/api/threads/{thread_id}/documents/{doc_id}").status_code == 204
