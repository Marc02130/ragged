"""UAT: review/evidence questions skip zwsp bibliography and return body text."""

import uuid

import httpx
import pytest

pytestmark = [pytest.mark.uat]

FIXTURE = """Purpose of review
Worldwide efforts continue to unravel the complex pathological pathways that lead to Alzheimer’s disease. The gut–brain–microbiome axis is emerging as a potential mechanism involved in Alzheimer’s disease pathogenesis.

Introduction
We hypothesize that gut microbes influence Alzheimer pathology via short-chain fatty acids.

Results
We found that treated mice had better memory scores than controls.

88.\t Loew EB, Sallis B (2023) The
“microbiome-gut-brain axis” in Alzheimer’s disease and its role in neurocognitive decline. Alzheimers Dement 19(S24):e083155. https://\u200bdoi.\u200borg/\u200b10.\u200b1002/\u200balz.\u200b083155

182. Vogt NM, et al. (2017) Gut microbiome alterations in Alzheimer’s disease. Sci Rep 7(1):13537. [PubMed: 29051531]
"""

QUESTION = (
    "review the documents and the evidence supporting their hypotheses, "
    "what hypotheses have the strongest hypotheses"
)


def test_review_question_skips_zwsp_bibliography(compose_stack: str) -> None:
    email = f"uat-rewrite-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=180.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "gut-ad notes"}).json()["id"]
        uploaded = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("notes.txt", FIXTURE.encode(), "text/plain"))],
        )
        assert uploaded.status_code == 201
        asked = client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": QUESTION},
        )
        assert asked.status_code == 200
        body = asked.json()["assistant_message"]
        sources = body.get("sources") or []
        joined = " ".join(s.get("content", "") for s in sources).lower()
        blob = (body["content"] + " " + joined).lower()
        assert "pubmed" not in joined
        assert "doi.org" not in joined.replace("\u200b", "")
        canned = "i don't have that in your documents."
        if body["content"].strip().lower() == canned:
            assert sources == []
        else:
            assert sources
            assert (
                "hypothesize" in blob
                or "we found" in blob
                or "gut" in blob
                or "microbiome" in blob
            )
