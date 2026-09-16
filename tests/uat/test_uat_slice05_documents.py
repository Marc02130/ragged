"""Slice 5 UAT: magic-byte reject on the live stack."""

import uuid

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice05,
    pytest.mark.skipif(not slice_ready(5), reason=skip_reason(5)),
]


def test_exe_renamed_pdf_is_415(compose_stack: str) -> None:
    email = f"uat-doc-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(base_url=compose_stack, timeout=30.0) as client:
        client.post(
            "/api/auth/register",
            json={"email": email, "password": "correct-horse-battery"},
        )
        thread_id = client.post("/api/threads", json={"title": "UAT docs"}).json()["id"]
        response = client.post(
            f"/api/threads/{thread_id}/documents",
            files=[("files", ("malware.pdf", b"MZ" + b"\x00" * 64, "application/pdf"))],
        )
        assert response.status_code == 415
        listed = client.get(f"/api/threads/{thread_id}/documents")
        assert listed.status_code == 200
        assert listed.json() == []
