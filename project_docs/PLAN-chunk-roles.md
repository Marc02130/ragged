# Plan: Chunk roles

## PR

**Title:** feat(api): chunk roles so queries skip citations and boilerplate

**Files:**

- `project_docs/PRD-chunk-roles.md`
- `project_docs/TECH-SPEC-chunk-roles.md`
- `project_docs/PLAN-chunk-roles.md`
- `api/app/services/classify.py`
- `api/app/services/rag.py`
- `api/app/services/chunk.py` (headings already on branch)
- `api/app/routers/documents.py`
- `api/app/prompts.py`
- `tests/unit/test_unit_classify.py`
- `tests/unit/test_unit_flexible_search.py`
- `tests/uat/test_uat_chunk_roles.py`
- `tests/dogfood/test_dogfood_chunk_roles.py`

**Depends on:** local MiniLM embeddings on `main`.

## Implementation order

1. `classify.py` + unit tests for descriptions, query maps, citation detection.
2. Ingest writes `role`; search filters; unlabeled classified on the fly.
3. Nearest-k fallback still skips citation/boilerplate.
4. UAT fixture: hypothesis paragraph + References block; evidence query must not return the DOI dump.
5. Dogfood: mechanisms question then “best evidence” returns non-canned answer when chunks exist.

## Verify

```bash
pytest -m unit
pytest -m "uat and not slice09"   # or full uat after compose rebuild
```
