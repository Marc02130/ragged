# Tech spec: Query rewrite, relative cutoff, citation override

**Status:** Implemented  
**Date:** 2026-09-19  
**Branch:** `feat/query-rewrite-relative-cutoff`

## Architecture

```
query:
  unique prior questions (up to 8) + current
  load_thread_corpus(title, files, headings)
  rewrite_query → {rewrite, aliases, hyde[lede, note]}
  embed original + rewrite + each hyde
  nearest-N per vector (no 0.4 cliff) ∪ ILIKE aliases
  drop citation/boilerplate (live classify overrides stored context)
  RRF union → relative_cut (best − 0.15) → expand short neighbors → grade
  if empty: retry embed rewrite+hyde+aliases only
  if still empty: canned refusal (sources [])
```

No new table. No dimension change. JSONB `metadata` unchanged.

## Rewrite (`api/app/services/rewrite.py`)

Prompt includes THREAD TITLE, FILES, HEADINGS. JSON:

```json
{"rewrite":"<standalone question in these documents' words>","aliases":["people","places","dates","nicknames"],"hyde":["<news lede>","<plain note>"]}
```

Skip the LLM when embeddings are stub or no chat key. Do **not** inject paper-only `we hypothesize` / `we found` aliases.

## Search (`api/app/services/rag.py`)

| Setting | Value |
| --- | --- |
| `WIDE_VECTOR_RESULTS` | 32 |
| `RELATIVE_SCORE_MARGIN` | 0.15 |
| `MAX_VECTOR_RESULTS` | 8 |
| `SIMILARITY_THRESHOLD` | unused as a keep gate |

`nearest_chunks` is the default pool. Roles add `ROLE_BOOST` (0.05); `excluded_roles` is citation/boilerplate only (never method/experience).

`grade_hits`: one chat call, `{"keep": [1, 3]}`. Stub embeddings skip grade. Empty keep list leaves the pool (do not canned on a parse miss).

## Classifier (`classify.py`)

`_norm` strips U+200B/C/D and BOM so `doi.org` matches. Numbered-ref headings, `[PubMed:` / PMID, two+ journal cite patterns → `citation`.

`resolve_role`: live citation/boilerplate wins over stored `context`. No re-upload required.

## Prompt

Ranking/review questions may synthesize from hypotheses and findings in SOURCES. Do not require a chunk that already states the ranking.

## Risks

- Grade adds one chat call per question when a key is configured.
- Over-eager citation heuristics could drop a methods table that looks like refs. Mitigation: live classify only promotes *to* citation, and grade can still keep body paragraphs.
- Rewrite without a key falls back to nearest-N on the raw question; citation override still applies.
