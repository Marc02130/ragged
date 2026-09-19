"""Query rewrite, HyDE parse, RRF, soft roles."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.classify import excluded_roles, preferred_roles
from app.services.rag import Hit, fuse_rrf
from app.services.rewrite import lexical_aliases, parse_plan, QueryPlan

pytestmark = [pytest.mark.unit]


def test_parse_plan_reads_json_and_fences() -> None:
    raw = """```json
    {"rewrite": "gut microbiome Alzheimer SCFA", "aliases": ["gut flora", "AD"], "hyde": "We found SCFAs."}
    ```"""
    plan = parse_plan(raw)
    assert "gut microbiome" in plan.rewrite
    assert "gut flora" in plan.aliases
    assert "SCFAs" in plan.hyde
    assert parse_plan("not json").rewrite == ""
    assert parse_plan("").aliases == []


def test_lexical_aliases_for_evidence_questions() -> None:
    aliases = lexical_aliases("what hypotheses have the strongest evidence")
    assert "hypothesize" in aliases
    assert "we found" in aliases
    assert lexical_aliases("what color is the sky") == []


def test_embed_texts_original_rewrite_hyde() -> None:
    plan = QueryPlan(rewrite="paper words", aliases=["gut flora"], hyde="We found X.")
    texts = plan.embed_texts("review the documents")
    assert texts[0] == "review the documents"
    assert "paper words" in texts
    assert "We found X." in texts


def test_how_does_this_work_does_not_exclude_method() -> None:
    assert "method" not in excluded_roles("how does this work")
    assert "citation" in excluded_roles("how does this work")
    assert "method" in preferred_roles("what HPLC instrumentation was used")


def test_fuse_rrf_unions_rankings_and_prefers_overlap() -> None:
    doc = uuid4()

    def hit(chunk_id, sim: float, role: str = "finding") -> Hit:
        return Hit(
            chunk_id=chunk_id,
            document_id=doc,
            file_name="paper.pdf",
            content="body",
            chunk_index=0,
            similarity=sim,
            role=role,
        )

    a, b, c = uuid4(), uuid4(), uuid4()
    fused = fuse_rrf(
        [[hit(a, 0.9), hit(b, 0.8)], [hit(c, 0.7), hit(a, 0.6)]],
        "what is this",
        "what is this",
    )
    ids = [row.chunk_id for row in fused]
    assert a in ids and b in ids and c in ids
    assert ids[0] == a


def test_answer_embeds_rewrite_and_hyde(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service
    from app.services.rewrite import QueryPlan
    from tests.unit.test_unit_slice06_messages import QUERY_VEC, _register_and_thread, _seed_chunk

    seen: list[list[str]] = []

    def fake_embed(texts: list[str], **_k: object) -> list[list[float]]:
        seen.append(list(texts))
        return [QUERY_VEC for _ in texts]

    monkeypatch.setattr(embeddings_service, "embed_texts", fake_embed)
    monkeypatch.setattr(
        rag_service,
        "rewrite_query",
        lambda *_a, **_k: QueryPlan(
            rewrite="gut microbiome SCFA Alzheimer hypothesis",
            aliases=["gut flora"],
            hyde="We found SCFAs alter blood-brain barrier integrity.",
        ),
    )
    monkeypatch.setattr(rag_service, "complete", lambda *_a, **_k: "from rewrite")
    user, thread_id = _register_and_thread(client)
    _seed_chunk(
        user["id"],
        thread_id,
        QUERY_VEC,
        content="We hypothesize that SCFAs alter blood-brain barrier integrity.",
    )
    response = client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "what hypotheses have the strongest evidence"},
    )
    assert response.status_code == 200
    assert seen
    assert len(seen[0]) == 3
    assert "gut microbiome SCFA" in seen[0][1]
    assert "We found SCFAs" in seen[0][2]
    assert response.json()["assistant_message"]["sources"]


def test_method_chunk_survives_how_does_this_work(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service
    from app.services.classify import classify_chunk
    from tests.unit.test_unit_slice06_messages import QUERY_VEC, _register_and_thread, _seed_chunk

    method_text = (
        "Non-parametric data were examined using the Mann-Whitney U-test. "
        "Statistical analyses were performed using GraphPad Prism 8.0."
    )
    assert classify_chunk(method_text) == "method"
    monkeypatch.setattr(embeddings_service, "embed_texts", lambda texts, **_k: [QUERY_VEC])
    monkeypatch.setattr(rag_service, "complete", lambda *_a, **_k: "from methods")
    user, thread_id = _register_and_thread(client)
    _seed_chunk(user["id"], thread_id, QUERY_VEC, content=method_text)
    response = client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "how does this work"},
    )
    assert response.status_code == 200
    joined = " ".join(
        s.get("content", "") for s in response.json()["assistant_message"]["sources"]
    )
    assert "GraphPad" in joined
