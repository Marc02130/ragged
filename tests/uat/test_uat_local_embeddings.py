"""UAT: ingest uses local MiniLM (384-d) without a user OpenAI key."""

import uuid

import httpx
import pytest

from tests import compose_support
from tests.paths import ROOT

pytestmark = [pytest.mark.uat]

SAMPLE_PDF = ROOT / "api" / "tests" / "fixtures" / "sample.pdf"


def test_vector_column_is_384(compose_stack: str) -> None:
    chunks = compose_support.psql(r"\d vector_chunks")
    assert "384" in chunks
    assert "1536" not in chunks


def test_upload_ready_without_user_openai_key(compose_stack: str) -> None:
    email = f"uat-embed-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=120.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "local embed"}).json()["id"]
        uploaded = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("sample.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
        )
        assert uploaded.status_code == 201
        doc = uploaded.json()[0]
        assert doc["status"] == "ready"
        assert "MiniLM" in (doc.get("embedding_model") or "")
