"""Chunk and query role labels from PRD descriptions."""

from __future__ import annotations

import pytest

from app.services.classify import (
    DEFAULT_RETRIEVE,
    ROLE_SPECS,
    allowed_roles,
    classify_chunk,
    classify_query,
    excluded_roles,
    preferred_roles,
    resolve_role,
)

pytestmark = [pytest.mark.unit]


def test_prd_roles_have_descriptions() -> None:
    for role in (
        "claim",
        "finding",
        "evaluation",
        "method",
        "context",
        "experience",
        "citation",
        "boilerplate",
    ):
        assert len(ROLE_SPECS[role]) > 40


def test_bibliography_is_citation() -> None:
    text = (
        "Tetzlaff J, Altman DG (2009) Preferred reporting items for systematic reviews. "
        "https://doi.org/10.1371/journal.pmed.1000097 et al. et al. et al."
    )
    assert classify_chunk(text, heading="References") == "citation"


def test_zwsp_doi_and_numbered_heading_are_citation() -> None:
    text = (
        "and inflammation-driven pathogenesis of Alzheimer’s Disease— a critical "
        "review. Mol Neurobiol 56(3):1841–1851. https://\u200bdoi.\u200borg/\u200b10.\u200b1007/"
        "s12035-018-1188-4\n145. Jiang C, Li G (2017) The gut microbiota"
    )
    heading = "88.\t Loew EB, Sallis B, Tracy M, Haran JP (2023) The"
    assert classify_chunk(text, heading=heading) == "citation"
    assert resolve_role(text, heading, stored="context") == "citation"


def test_pubmed_reference_list_is_citation() -> None:
    text = (
        "182. Vogt NM, et al. (2017) Gut microbiome alterations in Alzheimer’s disease. "
        "Sci Rep 7(1):13537. [PubMed: 29051531]"
    )
    assert classify_chunk(text, heading="Alzheimer’s disease. J Neuroinflammation 16(1):108.") == "citation"


def test_review_lede_is_not_citation() -> None:
    text = (
        "Worldwide efforts continue to unravel the complex pathological pathways "
        "that lead to Alzheimer’s disease. The gut–brain–microbiome axis is emerging "
        "as a potential mechanism involved in Alzheimer’s disease pathogenesis."
    )
    assert classify_chunk(text, heading="Purpose of review") != "citation"


def test_stats_methods_are_method() -> None:
    text = (
        "Non-parametric data were examined using the Mann-Whitney U-test. "
        "Statistical analyses were performed using GraphPad Prism 8.0."
    )
    assert classify_chunk(text, heading="") == "method"


def test_hypothesis_is_claim() -> None:
    assert classify_chunk("We hypothesize that SCFAs alter blood-brain barrier integrity.") == "claim"


def test_finding_keywords() -> None:
    assert classify_chunk("We found reduced Blautia was associated with elevated cytokines.") == "finding"


def test_personal_writing_is_experience() -> None:
    assert classify_chunk("This morning I felt foggy after the trip.", heading="Tuesday") == "experience"


def test_query_best_evidence_includes_context_excludes_citation() -> None:
    roles = allowed_roles("what hypotheses have the best evidence")
    assert "finding" in roles
    assert "claim" in roles
    assert "evaluation" in roles
    assert "context" in roles
    assert "citation" not in roles
    assert "boilerplate" not in roles


def test_evidence_review_query_includes_context() -> None:
    question = (
        "review the documents and the evidence supporting their hypotheses, "
        "what hypotheses have the strongest hypotheses"
    )
    roles = allowed_roles(question)
    assert "context" in roles
    assert "claim" in roles
    assert "finding" in roles
    assert "citation" not in roles


def test_query_instrumentation_includes_method() -> None:
    roles = allowed_roles("what HPLC instrumentation was used")
    assert "method" in roles
    assert "method" in preferred_roles("what HPLC instrumentation was used")


def test_evidence_query_does_not_hard_drop_method() -> None:
    excluded = excluded_roles("what hypotheses have the best evidence")
    assert "method" not in excluded
    assert "experience" not in excluded
    assert "citation" in excluded


def test_default_query_uses_retrieve_set() -> None:
    roles = classify_query("tell me about this")
    assert roles == DEFAULT_RETRIEVE


def test_evidence_query_drops_stored_context_bibliography(client, monkeypatch) -> None:
    import uuid

    from sqlalchemy import select

    from app import db
    from app.models import VectorChunk
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service
    from tests.unit.test_unit_slice06_messages import QUERY_VEC, _register_and_thread, _seed_chunk

    review = (
        "Worldwide efforts continue to unravel the complex pathological pathways "
        "that lead to Alzheimer’s disease. The gut–brain–microbiome axis is emerging "
        "as a potential mechanism involved in Alzheimer’s disease pathogenesis."
    )
    bib = (
        "182. Vogt NM, et al. (2017) Gut microbiome alterations in Alzheimer’s disease. "
        "Sci Rep 7(1):13537. [PubMed: 29051531] et al. et al."
    )
    monkeypatch.setattr(embeddings_service, "embed_texts", lambda texts, **_k: [QUERY_VEC])
    monkeypatch.setattr(rag_service, "complete", lambda *_a, **_k: "from review")
    user, thread_id = _register_and_thread(client)
    _seed_chunk(user["id"], thread_id, QUERY_VEC, content=review)
    _seed_chunk(user["id"], thread_id, QUERY_VEC, content=bib)
    with db.SessionLocal() as session:
        rows = session.scalars(
            select(VectorChunk).where(VectorChunk.thread_id == uuid.UUID(thread_id))
        )
        for chunk in rows:
            chunk.extra = {**dict(chunk.extra or {}), "role": "context"}
        session.commit()
    response = client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "what hypotheses have the strongest evidence"},
    )
    assert response.status_code == 200
    joined = " ".join(s.get("content", "") for s in response.json()["assistant_message"]["sources"])
    assert "gut–brain–microbiome" in joined or "gut-brain-microbiome" in joined
    assert "PubMed" not in joined


def test_evidence_query_retrieves_context_paragraph_not_citation(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service
    from app.services.classify import classify_chunk
    from tests.unit.test_unit_slice06_messages import QUERY_VEC, _register_and_thread, _seed_chunk

    context_text = (
        "These data suggest that SCFAs may modulate blood-brain barrier "
        "integrity via microglia."
    )
    citation_text = (
        "Tetzlaff J, Altman DG (2009) Preferred reporting items for systematic reviews. "
        "https://doi.org/10.1371/journal.pmed.1000097 et al. et al. et al."
    )
    assert classify_chunk(context_text) == "context"
    assert classify_chunk(citation_text, heading="References") == "citation"

    monkeypatch.setattr(embeddings_service, "embed_texts", lambda texts, **_k: [QUERY_VEC])
    monkeypatch.setattr(rag_service, "complete", lambda prompt, *_a, **_k: "from context")

    user, thread_id = _register_and_thread(client)
    _seed_chunk(user["id"], thread_id, QUERY_VEC, content=context_text)
    _seed_chunk(user["id"], thread_id, QUERY_VEC, content=citation_text)
    response = client.post(
        f"/api/threads/{thread_id}/messages",
        json={
            "content": (
                "review the documents and the evidence supporting their hypotheses, "
                "what hypotheses have the strongest hypotheses"
            )
        },
    )
    assert response.status_code == 200
    body = response.json()["assistant_message"]
    assert body["content"] == "from context"
    joined = " ".join(s.get("content", "") for s in body["sources"]).lower()
    assert "scfas" in joined
    assert "doi.org" not in joined
