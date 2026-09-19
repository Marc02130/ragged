from __future__ import annotations

import re

ROLES = (
    "claim",
    "finding",
    "evaluation",
    "method",
    "context",
    "experience",
    "citation",
    "boilerplate",
)

ROLE_SPECS: dict[str, str] = {
    "claim": (
        "What the author asserts, argues, hypothesizes, or believes. "
        "Opinions, theses, we propose, I think, editorial line, hypothesized mechanisms."
    ),
    "finding": (
        "What is reported as observed or having happened: results, facts, events, "
        "measurements, we found, significantly increased, the court found, sales rose."
    ),
    "evaluation": (
        "Judgment of strength or meaning: limitations, unconfirmed, strongest evidence, "
        "cannot establish causality, more research needed, conflicting reports."
    ),
    "method": (
        "How it was done or known: instruments, protocol, HPLC, statistics, ANOVA, "
        "sample collection, interview method, GraphPad, inclusion criteria."
    ),
    "context": (
        "Background the reader needs: setting, prior story, definitions, last year, "
        "literature narrative in the body, not a reference list."
    ),
    "experience": (
        "First-person lived detail: diary, memoir, anecdote, I felt, I remember, travel notes."
    ),
    "citation": (
        "Pointers to other works: bibliography, references, see Smith 2019, doi.org, "
        "http urls, et al author lists, footnote-only references."
    ),
    "boilerplate": (
        "Funding, ads, page headers, acknowledgements, competing interests, "
        "data availability on request, cookie copy."
    ),
}

DEFAULT_RETRIEVE = frozenset({"claim", "finding", "evaluation", "experience", "context"})
EXCLUDE_DEFAULT = frozenset({"citation", "boilerplate"})

_DOI = re.compile(r"\bdoi\.org\b|\b10\.\d{4,}/", re.I)
_ET_AL = re.compile(r"\bet al\.?\b", re.I)
_HTTP = re.compile(r"https?://", re.I)
_YEAR_CITE = re.compile(r"\([A-Z][A-Za-z\-]+,?\s+\d{4}\)")
_PUBMED = re.compile(r"\[pubmed:|\bpmid:\s*\d+", re.I)
_JOURNAL_CITE = re.compile(
    r"\b(j |mol |curr |aging |neurosci |alzheimer).{0,40}\d{4}[;:]",
    re.I,
)
_NUMBERED_REF_HEAD = re.compile(
    r"^\d+\s*\.?\s+[A-Z][A-Za-z\-]+.+(?:\d{4}|alzheimer|microbiome|gut)",
    re.I,
)
_ZWSP = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)


def _norm(text: str) -> str:
    return (text or "").translate(_ZWSP).lower()


def classify_chunk(text: str, heading: str = "") -> str:
    blob = f"{heading}\n{text}"
    low = _norm(blob)
    head = _norm(heading)

    if any(k in head for k in ("reference", "bibliograph", "works cited", "literature cited")):
        return "citation"
    if _NUMBERED_REF_HEAD.search(heading.strip()):
        return "citation"
    if any(k in head for k in ("acknowledg", "funding", "competing interest", "conflict of interest", "data availability")):
        return "boilerplate"
    if _DOI.search(blob) or _DOI.search(low) or _PUBMED.search(low):
        return "citation"
    if len(_ET_AL.findall(blob)) >= 3 and len(text) < 2500:
        return "citation"
    if low.startswith("http") or (len(_HTTP.findall(blob)) >= 3 and "we found" not in low):
        return "citation"
    if len(_JOURNAL_CITE.findall(low)) >= 2 and len(text) < 2500:
        return "citation"
    if any(k in low for k in ("graphpad prism", "bonferroni", "kruskal-wallis", "mann-whitney")) and not any(
        k in low for k in ("we found", "showed that", "associated with")
    ):
        return "method"
    if any(k in low for k in ("i felt", "i remember", "dear diary", "this morning i")):
        return "experience"
    if any(k in low for k in ("we hypothesize", "we propose", "it is hypothesized", "we argue")):
        return "claim"
    if any(
        k in low
        for k in ("we found", "was associated", "significantly", "these findings", "showed that")
    ):
        return "finding"
    if any(
        k in low
        for k in ("limitation", "cannot establish", "causal relationship cannot", "further studies")
    ):
        return "evaluation"

    scores = {role: 0 for role in ROLES}
    for role, spec in ROLE_SPECS.items():
        for word in spec.lower().split():
            word = word.strip(".,;:")
            if len(word) >= 5 and word in low:
                scores[role] += 1
    best = max(scores, key=lambda r: scores[r])
    if scores[best] >= 2:
        return best
    return "context"


_JUNK_PHRASES = (
    "substantial contributions to the conception",
    "final approval of the version to be published",
    "agreement to be accountable for all aspects",
    "competing interests",
    "data availability",
    "acknowledgements",
    "informed consent",
    "ethics committee",
)
_FIGURE_CAPTION = re.compile(
    r"\bfigure\s+\d+\b.*\b(illustrates|shows|flowchart|flow chart)\b",
    re.I | re.S,
)


def is_junk_chunk(text: str, heading: str = "") -> bool:
    """Drop before embed: captions, author-contribution, page numbers, citation soup."""
    piece = (text or "").strip()
    if len(piece) < 8:
        return True
    if re.fullmatch(r"[\d\s.\-]+", piece):
        return True
    low = _norm(f"{heading}\n{piece}")
    if any(p in low for p in _JUNK_PHRASES):
        return True
    if _FIGURE_CAPTION.search(piece):
        return True
    if classify_chunk(piece, heading) in EXCLUDE_DEFAULT:
        return True
    words = re.findall(r"[A-Za-z]{2,}", piece)
    digit_ratio = sum(c.isdigit() for c in piece) / max(len(piece), 1)
    if digit_ratio > 0.4 and len(words) < 40:
        return True
    return False


def classify_query(question: str) -> frozenset[str]:
    q = _norm(question)
    roles: set[str] = set()
    # Evidence / "strongest hypotheses": keep context. Heuristics label most
    # results/hypothesis prose as context; citation/boilerplate stay excluded.
    if any(k in q for k in ("evidence", "finding", "support", "strongest", "result", "observ")):
        return frozenset({"finding", "evaluation", "claim", "context"})
    if any(k in q for k in ("hypothes", "mechanism", "propos", "theor", "argue", "claim")):
        roles.update({"claim", "context", "evaluation"})
    if any(k in q for k in ("instrument", "protocol", "method", "how did they", "how was", "assay", "hplc", "statistic")):
        roles.update({"method"})
    if any(k in q for k in ("i feel", "i felt", "my diary", "personal", "anecdote")):
        roles.update({"experience", "context"})
    if any(k in q for k in ("reference", "bibliograph", "citation", "cited")):
        roles.update({"citation", "context"})
    if any(k in q for k in ("background", "what is known", "review the literature")):
        roles.update({"context", "claim"})
    if not roles:
        return DEFAULT_RETRIEVE
    return frozenset(roles)


def preferred_roles(question: str) -> frozenset[str]:
    """Roles to boost for this question. Not a hard allow-list."""
    wanted = classify_query(question)
    if wanted & EXCLUDE_DEFAULT:
        return wanted
    return frozenset(r for r in wanted if r not in EXCLUDE_DEFAULT) or DEFAULT_RETRIEVE


def excluded_roles(question: str) -> frozenset[str]:
    """Hard-drop citation/boilerplate unless asked. Never drop method or experience."""
    wanted = classify_query(question)
    dropped = frozenset(r for r in EXCLUDE_DEFAULT if r not in wanted)
    return dropped - {"method", "experience"}


def allowed_roles(question: str) -> frozenset[str]:
    return preferred_roles(question)


def resolve_role(text: str, heading: str, stored: str | None) -> str:
    live = classify_chunk(text, heading)
    if live in EXCLUDE_DEFAULT:
        return live
    if stored in ROLES:
        return stored
    return live
