"""Ingest drops junk; canned answers store no sources."""

from __future__ import annotations

import pytest

from app.services.classify import is_junk_chunk
from app.services.extract import extract_text

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _upload_root(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "UPLOAD_ROOT", str(tmp_path))
    return tmp_path


def test_icmje_contribution_is_junk() -> None:
    text = (
        "Substantial contributions to the conception or design of the work, the "
        "acquisition, analysis, or interpretation of data for the work; final approval "
        "of the version to be published; and agreement to be accountable for all aspects "
        "of the work in ensuring that questions related to the accuracy or integrity."
    )
    assert is_junk_chunk(text) is True


def test_figure_flowchart_caption_is_junk() -> None:
    text = "Figure 2 illustrates the flowchart of the method used for selecting the research. Literature search was conducted"
    assert is_junk_chunk(text) is True


def test_page_number_is_junk() -> None:
    assert is_junk_chunk("4") is True


def test_hypothesis_paragraph_is_kept() -> None:
    text = (
        "We hypothesize that gut microbial metabolites including short-chain fatty acids "
        "alter blood-brain barrier integrity and thereby influence Alzheimer pathology."
    )
    assert is_junk_chunk(text) is False


def test_sample_pdf_still_extracts() -> None:
    from tests.paths import ROOT

    data = (ROOT / "api" / "tests" / "fixtures" / "sample.pdf").read_bytes()
    text = extract_text(data, "pdf")
    assert "hello" in text.lower() or "ragged" in text.lower()


def test_all_junk_upload_is_422(client) -> None:
    from tests.unit.test_unit_slice06_messages import _register_and_thread

    _, thread_id = _register_and_thread(client)
    junk = (
        "Substantial contributions to the conception or design of the work, the "
        "acquisition, analysis, or interpretation of data; final approval of the "
        "version to be published; and agreement to be accountable for all aspects.\n"
    )
    response = client.post(
        f"/api/threads/{thread_id}/documents",
        files=[("files", ("contrib.txt", junk.encode(), "text/plain"))],
    )
    assert response.status_code == 422
    assert "no usable text" in response.json()["detail"].lower()


def test_canned_answer_stores_no_sources(client, monkeypatch) -> None:
    from app.prompts import CANNED_REFUSAL
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service
    from tests.unit.test_unit_slice06_messages import QUERY_VEC, _register_and_thread, _seed_chunk

    monkeypatch.setattr(embeddings_service, "embed_texts", lambda texts, **_k: [QUERY_VEC])
    monkeypatch.setattr(rag_service, "complete", lambda *_a, **_k: CANNED_REFUSAL)
    user, thread_id = _register_and_thread(client)
    _seed_chunk(user["id"], thread_id, QUERY_VEC, content="We hypothesize SCFAs affect AD.")
    response = client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "what hypotheses have the best evidence"},
    )
    assert response.status_code == 200
    assert response.json()["assistant_message"]["content"] == CANNED_REFUSAL
    assert response.json()["assistant_message"]["sources"] == []
