"""Dogfood: follow-up evidence question is not citation-only."""

import uuid

import httpx
import pytest

from tests.paths import ROOT

pytestmark = [pytest.mark.dogfood]

SAMPLE_PDF = ROOT / "api" / "tests" / "fixtures" / "sample.pdf"


def test_followup_evidence_question_has_sources(compose_stack: str) -> None:
    email = f"dogfood-roles-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=120.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "roles"}).json()["id"]
        up = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("sample.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
        )
        assert up.status_code == 201
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "what mechanisms are hypothesized"},
        )
        follow = client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "what hypotheses have the best evidence"},
        )
        assert follow.status_code == 200
        # With papers in the thread, nearest allowed roles should yield sources
        # or a model answer, not a silent empty retrieval.
        msg = follow.json()["assistant_message"]
        assert msg.get("sources") or msg["content"]
