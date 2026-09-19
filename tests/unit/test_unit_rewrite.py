"""Query rewrite, HyDE parse, RRF, relative cut, soft roles."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.classify import excluded_roles, preferred_roles
from app.services.rag import Hit, fuse_rrf, relative_cut
from app.services.rewrite import QueryPlan, ThreadCorpus, build_rewrite_prompt, parse_plan

pytestmark = [pytest.mark.unit]


def test_parse_plan_reads_json_and_two_hyde_registers() -> None:
    raw = """```json
    {
      "rewrite": "Did the Globe cover the Ottawa housing vote?",
      "aliases": ["Ottawa", "Jane Doe"],
      "hyde": ["City council voted on housing Tuesday.", "I saw Jane's note about the vote."]
    }
    ```"""
    plan = parse_plan(raw)
    assert "Ottawa" in plan.rewrite
    assert "Jane Doe" in plan.aliases
    assert len(plan.hyde) == 2
    assert "council" in plan.hyde[0]
    assert "Jane" in plan.hyde[1]
    assert parse_plan("not json").rewrite == ""
    assert parse_plan("").hyde == []


def test_parse_plan_accepts_single_hyde_string() -> None:
    plan = parse_plan('{"rewrite": "q", "aliases": [], "hyde": "A short note."}')
    assert plan.hyde == ["A short note."]


def test_embed_texts_original_rewrite_and_two_hydes() -> None:
    plan = QueryPlan(
        rewrite="standalone question",
        aliases=["Ottawa"],
        hyde=["News lede here.", "Plain note here."],
    )
    texts = plan.embed_texts("review the documents")
    assert texts[0] == "review the documents"
    assert "standalone question" in texts
    assert "News lede here." in texts
    assert "Plain note here." in texts
    assert plan.embed_texts("") == [
        "standalone question",
        "News lede here.",
        "Plain note here.",
    ]


def test_rewrite_prompt_includes_thread_title_and_headings() -> None:
    prompt = build_rewrite_prompt(
        "what happened?",
        ["earlier ask"],
        ThreadCorpus(title="Ottawa notes", files=["clip.txt"], headings=["City Hall"]),
    )
    assert "Ottawa notes" in prompt
    assert "clip.txt" in prompt
    assert "City Hall" in prompt
    assert "news lede" in prompt.lower()
    assert "scientific abstract" in prompt.lower()
    assert "hypothetical abstract" not in prompt.lower()


def test_how_does_this_work_does_not_exclude_method() -> None:
    assert "method" not in excluded_roles("how does this work")
    assert "experience" not in excluded_roles("how does this work")
    assert "citation" in excluded_roles("how does this work")
    assert "method" in preferred_roles("what HPLC instrumentation was used")


def test_never_drop_method_or_experience_on_evidence_query() -> None:
    excluded = excluded_roles("what hypotheses have the strongest evidence")
    assert "method" not in excluded
    assert "experience" not in excluded
    assert "citation" in excluded
    assert "boilerplate" in excluded


def test_parse_keep_reads_json() -> None:
    from app.services.rag import _parse_keep

    assert _parse_keep('{"keep": [1, 3, 3, 9]}', 4) == [1, 3]
    assert _parse_keep("nope", 4) == []


def test_relative_cut_keeps_near_best_not_absolute_floor() -> None:
    doc = uuid4()

    def hit(sim: float) -> Hit:
        return Hit(
            chunk_id=uuid4(),
            document_id=doc,
            file_name="a.pdf",
            content="body",
            chunk_index=0,
            similarity=sim,
            role="context",
        )

    kept = relative_cut([hit(0.31), hit(0.28), hit(0.10)])
    scores = sorted((row.similarity for row in kept), reverse=True)
    assert scores[0] == pytest.approx(0.31)
    assert 0.28 in scores
    assert 0.10 not in scores


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
            rewrite="Did gut microbes affect memory in these files?",
            aliases=["Alzheimer"],
            hyde=[
                "Researchers linked gut microbes to memory loss.",
                "I keep thinking the gut notes explain the memory fog.",
            ],
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
    assert len(seen[0]) == 4
    assert "Did gut microbes affect memory" in seen[0][1]
    assert "Researchers linked gut microbes" in seen[0][2]
    assert "memory fog" in seen[0][3]
    assert response.json()["assistant_message"]["sources"]


def test_empty_pool_retries_rewrite_before_canned(client, monkeypatch) -> None:
    from app.services import embeddings as embeddings_service
    from app.services import rag as rag_service
    from app.services.rewrite import QueryPlan
    from tests.unit.test_unit_slice06_messages import QUERY_VEC, _register_and_thread

    seen: list[list[str]] = []

    def fake_embed(texts: list[str], **_k: object) -> list[list[float]]:
        seen.append(list(texts))
        return [QUERY_VEC for _ in texts]

    monkeypatch.setattr(embeddings_service, "embed_texts", fake_embed)
    monkeypatch.setattr(
        rag_service,
        "rewrite_query",
        lambda *_a, **_k: QueryPlan(
            rewrite="rewritten standalone question",
            aliases=["Ottawa"],
            hyde=["News lede.", "Plain note."],
        ),
    )
    called = {"chat": 0}

    def boom(_prompt: str, *_args, **_kwargs) -> str:
        called["chat"] += 1
        raise AssertionError("chat should not be called")

    monkeypatch.setattr(rag_service, "complete", boom)
    _, thread_id = _register_and_thread(client)
    response = client.post(
        f"/api/threads/{thread_id}/messages", json={"content": "review the documents"}
    )
    assert response.status_code == 200
    assert response.json()["assistant_message"]["content"] == (
        "I don't have that in your documents."
    )
    assert called["chat"] == 0
    assert len(seen) == 2
    assert "rewritten standalone question" in seen[0]
    assert seen[1][0] == "rewritten standalone question"
    assert "review the documents" not in seen[1]


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
