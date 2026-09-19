"""Generic headings, query expansion, not IMRaD-only routing."""

from __future__ import annotations

import pytest

from app.services.chunk import (
    expand_query,
    heading_boost,
    looks_like_heading,
    query_terms,
    split_with_headings,
    unique_questions,
)

pytestmark = [pytest.mark.unit]


def test_headings_are_taken_from_the_paper_not_a_fixed_list() -> None:
    text = (
        "Instrumentation\n"
        "We used a custom HPLC stack for bile acids.\n\n"
        "Field Notes\n"
        "Soil samples were stored at -80C.\n"
    )
    labeled = split_with_headings(text, chunk_size=400, overlap=0)
    headings = {heading for _piece, heading in labeled}
    assert "Instrumentation" in headings
    assert "Field Notes" in headings
    assert looks_like_heading("2.1 Sample Preparation")
    assert not looks_like_heading(
        "This long sentence about methods should not be treated as a heading."
    )


def test_instrumentation_query_boosts_matching_heading() -> None:
    boost = heading_boost("Instrumentation", "what HPLC instrumentation was used?", "")
    assert boost >= 0.12
    assert heading_boost("Introduction", "what HPLC instrumentation was used?", "") == 0.0


def test_expand_query_keeps_followup_on_topic() -> None:
    expanded = expand_query(
        "what hypotheses have the best evidence?",
        ["how does the gut biome influence alzheimer development"],
    )
    assert "gut biome" in expanded
    assert "best evidence" in expanded
    assert query_terms("what is the best evidence") == ["evidence"]


def test_unique_questions_drops_repeated_followups() -> None:
    questions = [
        "how does the gut biome influence alzheimer development",
        "review the documents and the evidence supporting their hypotheses",
        "review the documents and the evidence supporting their hypotheses",
        "review the documents and the evidence supporting their hypotheses",
    ]
    unique = unique_questions(questions, limit=8)
    assert len(unique) == 2
    assert unique[0].startswith("how does the gut")
    terms = query_terms("evidence", "hypothesize", "we found", limit=16)
    assert "hypothesize" in terms
    assert "found" in terms


def test_followup_embeds_expanded_text(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service
    from tests.unit.test_unit_slice06_messages import QUERY_VEC, _register_and_thread, _seed_chunk

    seen: list[str] = []

    def fake_embed(texts: list[str], **_k: object) -> list[list[float]]:
        seen.append(texts[0])
        return [QUERY_VEC]

    monkeypatch.setattr(embeddings_service, "embed_texts", fake_embed)
    monkeypatch.setattr(rag_service, "complete", lambda prompt, *_a, **_k: "ok")
    user, thread_id = _register_and_thread(client)
    _seed_chunk(user["id"], thread_id, QUERY_VEC, content="gut microbiome and AD")
    client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "how does the gut biome influence alzheimer development"},
    )
    client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "what hypotheses have the best evidence?"},
    )
    assert any("gut biome" in text and "best evidence" in text for text in seen)
