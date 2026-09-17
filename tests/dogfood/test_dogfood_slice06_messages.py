"""Slice 6 dogfood: in-corpus question and out-of-corpus refusal."""

import uuid

import httpx
import pytest

from tests.paths import ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice06,
    pytest.mark.skipif(not slice_ready(6), reason=skip_reason(6)),
]

CANNED = "I don't have that in your documents."
SAMPLE_PDF = ROOT / "api" / "tests" / "fixtures" / "sample.pdf"


def test_operator_asks_in_and_out_of_corpus(compose_stack: str) -> None:
    email = f"dogfood-msg-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=60.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        filled = client.post("/api/threads", json={"title": "with pdf"}).json()["id"]
        uploaded = client.post(
            f"/api/threads/{filled}/documents",
            files=[("files", ("sample.pdf", SAMPLE_PDF.read_bytes(), "application/pdf"))],
        )
        assert uploaded.status_code == 201
        asked = client.post(
            f"/api/threads/{filled}/messages",
            json={"content": "what does the document say?"},
        )
        assert asked.status_code == 200
        assert asked.json()["assistant_message"]["content"] != CANNED
        assert asked.json()["assistant_message"]["sources"]

        empty = client.post("/api/threads", json={"title": "empty"}).json()["id"]
        refused = client.post(
            f"/api/threads/{empty}/messages",
            json={"content": "what is the meaning of life?"},
        )
        assert refused.status_code == 200
        assert refused.json()["assistant_message"]["content"] == CANNED
        assert refused.json()["assistant_message"]["sources"] == []
