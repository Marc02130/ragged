"""UAT: junk chunks are not stored; evidence query omits bibliography."""

import uuid

import httpx
import pytest

pytestmark = [pytest.mark.uat]

FIXTURE = """Introduction
We hypothesize that gut microbes influence Alzheimer pathology via short-chain fatty acids.

Results
We found that treated mice had better memory scores than controls.

Substantial contributions to the conception or design of the work, the acquisition,
analysis, or interpretation of data for the work; final approval of the version to be published.

Figure 2 illustrates the flowchart of the method used for selecting the research.

References
Tetzlaff J (2009) PRISMA. https://doi.org/10.1371/journal.pmed.1000097 et al. et al. et al.
"""


def test_evidence_query_skips_junk_and_references(compose_stack: str) -> None:
    email = f"uat-junk-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=120.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "junk"}).json()["id"]
        uploaded = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("note.txt", FIXTURE.encode(), "text/plain"))],
        )
        assert uploaded.status_code == 201
        asked = client.post(
            f"/api/threads/{thread_id}/messages",
            json={"content": "what hypotheses have the best evidence"},
        )
        assert asked.status_code == 200
        body = asked.json()["assistant_message"]
        blob = (body["content"] + " " + str(body.get("sources"))).lower()
        assert "doi.org" not in blob
        assert "substantial contributions" not in blob
        assert "flowchart" not in blob
        if body["content"].strip() == "I don't have that in your documents.":
            assert body.get("sources") == []


def test_all_junk_upload_is_422(compose_stack: str) -> None:
    junk = (
        "Substantial contributions to the conception or design of the work, the "
        "acquisition, analysis, or interpretation of data for the work; final approval "
        "of the version to be published; and agreement to be accountable for all aspects.\n"
    )
    email = f"uat-junk422-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=60.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "junk422"}).json()["id"]
        uploaded = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("contrib.txt", junk.encode(), "text/plain"))],
        )
        assert uploaded.status_code == 422
        assert "no usable text" in uploaded.json()["detail"].lower()
