# Tech spec: Chunk roles

**Status:** Draft  
**Date:** 2026-09-17

## Architecture

```
ingest:  extract → heading split → classify_chunk(text, heading) → embed → vector_chunks.metadata {heading, role}
query:   expand with last 2 user turns → classify_query(question) → vector + lexical search
         → drop roles not in the query set (citation/boilerplate unless requested)
         → if empty, nearest-k among allowed roles
         → if still empty, canned refusal
```

Roles live in existing JSONB `vector_chunks.metadata`. No new table. No dimension change.

## Classifier (`api/app/services/classify.py`)

`ROLE_SPECS`: id → description (same strings as the PRD).

**Chunk label** (no chat key):

1. Heading/body heuristics (References, doi.org, “et al.” density, GraphPad/ANOVA-only, first-person experience, “we hypothesize”, “we found”, funding/acknowledgements).
2. Else keyword overlap with each role **description**.
3. Else `context`.

**Query label:**

1. Keyword map from the question (evidence/strongest → finding+evaluation+claim; instrument/protocol → method; …).
2. Else default retrieve set: claim, finding, evaluation, experience, context.

Descriptions are the source of keywords and the future LLM prompt. MiniLM similarity to descriptions is optional later; v1 does not require it so tests and stub embeddings stay deterministic.

## Search changes (`rag.py`)

- `Hit.role`
- SQL still cosine + lexical; Python drops disallowed roles (including on-the-fly classify when `metadata.role` is missing).
- Nearest-k fallback also excludes citation/boilerplate unless requested.
- Prompt lists `role` and `heading` as location hints only.

## Ingest (`documents.py`)

`extra = {heading, role}` on every chunk.

## Compatibility

Old chunks without `role` are classified at read time. Users do not have to re-upload for the filter to work. Re-upload still improves heading prefixes in the embedding.

## Risks

- Heuristics mislabel a results table as method: query “best evidence” might miss a table. Mitigation: “finding” keywords (p <, significantly, increased) win over method if both match.
- Over-filtering: if every chunk is citation, fallback nearest-k among non-citation; if all citation, canned is correct.
