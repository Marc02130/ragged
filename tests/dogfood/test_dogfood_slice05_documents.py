"""Slice 5 dogfood: upload a small PDF and see status ready."""

import uuid

import httpx
import pytest

from tests.paths import ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice05,
    pytest.mark.skipif(not slice_ready(5), reason=skip_reason(5)),
]

SAMPLE_PDF = ROOT / "api" / "tests" / "fixtures" / "sample.pdf"


def test_operator_uploads_a_pdf(compose_stack: str) -> None:
    email = f"dogfood-doc-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=60.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "Lab PDF"}).json()["id"]
        response = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("sample.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
        )
        assert response.status_code == 201
        doc = response.json()[0]
        assert doc["status"] == "ready"
        assert doc["chunk_count"] >= 1
        listed = client.get(f"/api/threads/{thread_id}/documents")
        assert listed.json()[0]["id"] == doc["id"]
        assert "content" not in listed.json()[0]
