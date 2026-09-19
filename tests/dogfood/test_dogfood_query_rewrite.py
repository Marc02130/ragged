"""Dogfood: review/strongest-hypotheses follow-up is not citation-only."""

import uuid

import httpx
import pytest

pytestmark = [pytest.mark.dogfood]

FIXTURE = """Purpose of review
Worldwide efforts continue to unravel the complex pathological pathways that lead to Alzheimer’s disease. The gut–brain–microbiome axis is emerging as a potential mechanism.

Introduction
We hypothesize that gut microbes influence Alzheimer pathology via short-chain fatty acids.

Results
We found that treated mice had better memory scores than controls.

182. Vogt NM, et al. (2017) Gut microbiome alterations in Alzheimer’s disease. Sci Rep 7(1):13537. [PubMed: 29051531]
"""


def test_followup_review_question_has_body_sources(compose_stack: str) -> None:
    email = f"dogfood-rewrite-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=180.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "research"}).json()["id"]
        up = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("notes.txt", FIXTURE.encode(), "text/plain"))],
        )
        assert up.status_code == 201
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "what mechanisms are hypothesized"},
        )
        follow = client.post(
            f"/api/threads/{thread_id}/messages",
            json={
                "content": (
                    "review the documents and the evidence supporting their hypotheses, "
                    "what hypotheses have the strongest hypotheses"
                )
            },
        )
        assert follow.status_code == 200
        msg = follow.json()["assistant_message"]
        sources = msg.get("sources") or []
        joined = " ".join(s.get("content", "") for s in sources).lower()
        assert "pubmed" not in joined
        assert sources or msg["content"]
        if msg["content"].strip() != "I don't have that in your documents.":
            assert sources
            assert "pubmed" not in joined
