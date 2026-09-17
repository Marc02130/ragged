"""Chunk and query role labels from PRD descriptions."""

from __future__ import annotations

import pytest

from app.services.classify import (
    DEFAULT_RETRIEVE,
    ROLE_SPECS,
    allowed_roles,
    classify_chunk,
    classify_query,
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


def test_query_best_evidence_excludes_citation() -> None:
    roles = allowed_roles("what hypotheses have the best evidence")
    assert "finding" in roles
    assert "claim" in roles
    assert "citation" not in roles
    assert "boilerplate" not in roles


def test_query_instrumentation_includes_method() -> None:
    roles = allowed_roles("what HPLC instrumentation was used")
    assert "method" in roles


def test_default_query_uses_retrieve_set() -> None:
    roles = classify_query("tell me about this")
    assert roles == DEFAULT_RETRIEVE
