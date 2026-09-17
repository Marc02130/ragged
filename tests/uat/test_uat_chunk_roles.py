"""UAT: evidence queries do not surface bibliography chunks."""

import uuid

import httpx
import pytest

pytestmark = [pytest.mark.uat]

FIXTURE = """Introduction
We hypothesize that gut microbes influence Alzheimer pathology via SCFAs.

Results
We found that treated mice had better memory scores than controls.

References
Tetzlaff J, Altman DG (2009) PRISMA. https://doi.org/10.1371/journal.pmed.1000097
Liu P et al. (2019) Altered microbiomes. https://doi.org/10.1016/j.bbi.2019.05.008 et al. et al.
"""


def test_evidence_query_skips_reference_block(compose_stack: str) -> None:
    email = f"uat-roles-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=120.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "roles"}).json()["id"]
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
        assert "doi.org/10.1371" not in blob
        assert "i don't have that in your documents." not in body["content"].lower() or body.get(
            "sources"
        )
        sources = body.get("sources") or []
        joined = " ".join(s.get("content", "") for s in sources).lower()
        assert "doi.org" not in joined
        assert "hypothesize" in joined or "we found" in joined or sources == []
