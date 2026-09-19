# Plan: Query rewrite, relative cutoff, citation override

## PR

**Title:** feat(api): corpus-conditioned rewrite, relative cutoff, citation override

**Files:**

- `project_docs/PRD-query-rewrite.md`
- `project_docs/TECH-SPEC-query-rewrite.md`
- `project_docs/PLAN-query-rewrite.md`
- `api/app/config.py`
- `api/app/services/rewrite.py`
- `api/app/services/rag.py`
- `api/app/services/classify.py`
- `api/app/prompts.py`
- `tests/unit/test_unit_rewrite.py`
- `tests/unit/test_unit_classify.py`
- `tests/unit/test_unit_slice06_messages.py`
- `tests/uat/test_uat_query_rewrite.py`
- `tests/dogfood/test_dogfood_query_rewrite.py`

**Depends on:** junk filter + sequential upload on `main`.

## Implementation order

1. Corpus-conditioned rewrite (title/files/headings; news lede + plain note HyDE). Delete paper-only `lexical_aliases`.
2. Nearest-N default pool + relative 0.15 cut; retry rewrite+aliases before canned.
3. Roles as boosts; never drop method/experience.
4. Query-time citation override (zwsp DOI, PubMed, numbered-ref headings).
5. Neighbor expand + cheap grade.
6. UAT fixture: review lede + hypothesis + zwsp bibliography.
7. Dogfood: mechanisms then “review the documents / strongest hypotheses”.

## Later (not this branch)

Ingest characterization, Postgres FTS, BGE-small re-embed, grade-then-rewrite loop beyond the one retry already in `answer()`.

## Verify

```bash
pytest tests/unit/test_unit_rewrite.py tests/unit/test_unit_classify.py
pytest -m uat -k query_rewrite
pytest -m dogfood -k query_rewrite
```
