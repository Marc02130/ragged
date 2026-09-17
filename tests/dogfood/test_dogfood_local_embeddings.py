"""Dogfood: upload a PDF; local MiniLM marks it ready."""

import uuid

import httpx
import pytest

from tests.paths import ROOT

pytestmark = [pytest.mark.dogfood]

SAMPLE_PDF = ROOT / "api" / "tests" / "fixtures" / "sample.pdf"


def test_operator_upload_uses_local_minilm(compose_stack: str) -> None:
    email = f"dogfood-embed-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=120.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "MiniLM"}).json()["id"]
        uploaded = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("sample.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
        )
        assert uploaded.status_code == 201
        assert uploaded.json()[0]["status"] == "ready"
        assert "MiniLM" in uploaded.json()[0]["embedding_model"]
