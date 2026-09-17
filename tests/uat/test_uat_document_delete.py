"""UAT: owner can delete a document; it disappears from the list."""

import uuid

import httpx
import pytest

from tests.paths import ROOT

pytestmark = [pytest.mark.uat]

SAMPLE_PDF = ROOT / "api" / "tests" / "fixtures" / "sample.pdf"


def test_delete_document_from_thread(compose_stack: str) -> None:
    email = f"uat-del-{uuid.uuid4().hex[:8]}@example.com"
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
        assert client.get(f"/api/threads/{thread_id}/documents").json() == []
