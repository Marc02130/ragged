# Query rewrite / relative cutoff — test results

- **Branch:** `feat/query-rewrite-relative-cutoff`
- **Date:** 2026-09-18 (America/New_York)
- **Gate:** **PASS** (unit, UAT, dogfood)
- **Authority:** Initial author run on Mac compose; re-verified by Ragged QA (UAT) + Ragged Dogfood (pytest dogfood) on Mac checkout `/Users/marcbreneiser/Code/ragged/` 2026-09-18 evening.

## Feature summary

Query path only (no schema change, no re-ingest):

1. **Rewrite:** Thread title, file names, and headings go into the rewrite prompt. JSON is a standalone question, name/place/date aliases, and two HyDEs (news lede + plain note). Paper-only `we hypothesize` / `we found` aliases are gone.
2. **Nearest-N + relative cut:** Default pool is wide nearest-32 with no 0.4 cliff. Keep hits within `RELATIVE_SCORE_MARGIN` (0.15) of the best cosine. RRF unions original + rewrite + HyDE.
3. **Retry:** Empty pool retries once with rewrite + aliases before canned.
4. **Roles:** Boost only. Hard-drop citation/boilerplate. Never drop method or experience.
5. **Citation override:** Live classify wins over stored `context` for zwsp `doi.org`, `[PubMed:]`, numbered-ref headings, journal cite soup.
6. **Grade / neighbors:** Short title hits expand to adjacent chunks. One cheap grade call drops leftover bibliography when a chat key is present.

## Commands

```bash
cd /Users/marcbreneiser/Code/ragged
git checkout feat/query-rewrite-relative-cutoff
source api/.venv/bin/activate   # or ./api/.venv/bin/python -m pytest
export RAG_KEEP_COMPOSE=1
pytest tests/unit --tb=short
pytest tests/uat/test_uat_query_rewrite.py tests/dogfood/test_dogfood_query_rewrite.py -m 'uat or dogfood' -v --tb=short
```

## Unit

- Full `tests/unit`: **98 passed**, ~10.5s
- Focused `test_unit_rewrite.py` + `test_unit_classify.py` + `test_unit_slice06_messages.py`: **34 passed**

Key assertions:

- Two HyDE registers parse; embed list is original + rewrite + lede + note
- Rewrite prompt includes thread title/files/headings and forbids “hypothetical abstract”
- Relative cut keeps 0.28 when best is 0.31; drops 0.10
- Empty pool retries rewrite-only embed before canned; chat is not called
- zwsp DOI / numbered-ref heading / PubMed → `citation`; `resolve_role(..., stored="context")` still citation
- Review lede (“Purpose of review”) is not citation
- Evidence query never excludes method/experience
- Stored-context bibliography is omitted from message sources; review paragraph is kept
- `RELATIVE_SCORE_MARGIN == 0.15`

## UAT

- `tests/uat/test_uat_query_rewrite.py::test_review_question_skips_zwsp_bibliography`: **PASSED** (~3s with stack already up)

Fixture: Purpose-of-review lede + hypothesis + results + zwsp DOI numbered ref + PubMed line. Question: “review the documents and the evidence supporting their hypotheses, what hypotheses have the strongest hypotheses”.

- Sources must not contain `pubmed` or `doi.org`
- If canned, `sources == []`; otherwise sources exist and mention hypothesize / we found / gut / microbiome

## Dogfood

- `tests/dogfood/test_dogfood_query_rewrite.py::test_followup_review_question_has_body_sources`: **PASSED**
- Live operator: same question on thread `research` (20 PDFs) returned a non-canned answer after citation override + grade (2026-09-18 evening)

Suggested UI check: canned replies still hide Sources; successful review answers cite body paragraphs, not numbered reference lists.

## Open / later

- Ingest characterization, Postgres FTS, BGE-small re-embed — not this branch
- Grade is an extra chat call when a key is configured

## Ragged Testing verification (2026-09-18 ~22:00 ET)

- **UAT (Ragged QA, Mac):** full `tests/uat` — **24 passed**, 1 skipped; focused `test_uat_query_rewrite.py` — **PASSED**
- **Dogfood (Ragged Dogfood, Mac):** `test_dogfood_query_rewrite.py` — **PASSED** (follow-up review/strongest-hypotheses → body sources, no PubMed in source text); `test_dogfood_junk_filter.py` canned empty sources — **PASSED**
- **Gate:** **PASS** — no open product bugs on this feature
