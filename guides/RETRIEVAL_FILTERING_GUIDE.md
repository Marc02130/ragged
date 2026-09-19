# Retrieval Filtering Guide

RAGged retrieves document chunks only from the authenticated user's selected thread. It does not search other threads, vectorized chat history, or archived conversation snapshots.

## Ingest-time filtering

`api/app/routers/documents.py` extracts text, splits it with heading context, and drops junk before embedding. `api/app/services/classify.py` treats the following as junk:

- empty, very short, page-number-like, or digit-heavy fragments;
- common author-contribution, acknowledgements, funding, conflict, data-availability, consent, and ethics boilerplate;
- selected figure captions;
- chunks classified as citation or boilerplate.

A document with no chunks after filtering is marked `failed`. If every file in one upload request fails, the endpoint returns `422`; a mixed ready/failed request returns `201` with each document's status.

Each retained chunk stores its nearest heading and one role: `claim`, `finding`, `evaluation`, `method`, `context`, `experience`, `citation`, or `boilerplate`.

## Candidate retrieval

For each original/rewrite/HyDE embedding, `nearest_chunks`:

1. selects up to `max(WIDE_VECTOR_RESULTS, MAX_VECTOR_RESULTS * 4)` nearest chunks by pgvector cosine distance;
2. filters by `user_id`, `thread_id`, and the configured embedding model;
3. reclassifies each candidate at query time with `resolve_role`;
4. drops citation and boilerplate unless the question explicitly asks for them;
5. adds lexical candidates whose content or heading matches selected query/rewrite terms;
6. ranks the pool by cosine similarity plus heading and role boosts.

Query-time reclassification is intentional. DOI links, PubMed/PMID markers, citation-heavy journal text, and zero-width-character-obfuscated DOI text can override a stale stored role.

## Boosts, not hard allow-lists

Question classification chooses preferred roles. A preferred role adds `0.05` to pool ordering; a heading containing query terms adds up to `0.24`. These are boosts. Method, experience, context, claims, findings, and evaluations are not discarded merely because another role is preferred.

Citation and boilerplate are hard drops by default. An explicit citation/reference/bibliography question can retain citations. Boilerplate remains excluded unless its role is explicitly requested by the classifier.

## Fusion and relative cutoff

RAGged combines the original, rewrite, and HyDE rankings with reciprocal rank fusion:

```text
rrf_score(chunk) = sum(1 / (60 + rank + 1))
```

It then finds the best raw cosine similarity among fused hits and keeps hits satisfying:

```text
hit.similarity >= best_similarity - RELATIVE_SCORE_MARGIN
```

The default margin is `0.15`; the final default cap is eight hits. `SIMILARITY_THRESHOLD` remains in configuration for compatibility but is not used by the current retrieval path. This is a relative cutoff, not a fixed `0.4` similarity cliff.

Short retained fragments can pull in adjacent chunks from the same document. If multiple hits remain and a chat key is available, a small grading call can reject bibliography, author-list, and title-only leftovers. A grading failure leaves the existing hits unchanged.

## Configuration

The relevant server settings are in `api/app/config.py`:

| Setting | Default | Purpose |
| --- | ---: | --- |
| `WIDE_VECTOR_RESULTS` | 32 | Nearest candidates per embedding before fusion |
| `MAX_VECTOR_RESULTS` | 8 | Maximum sources after filtering |
| `RELATIVE_SCORE_MARGIN` | 0.15 | Allowed cosine gap from the best hit |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Required model tag for searchable chunks |

These values are operator settings; the message request cannot override them.

## Troubleshooting retrieval

- Confirm the document status is `ready` and `chunk_count` is nonzero.
- Confirm the query is sent to the same thread that owns the document.
- Confirm old chunks use the current `EMBEDDING_MODEL`; retrieval excludes another model tag.
- Inspect stored chunk `metadata` for headings and roles.
- For a suspected citation leak, compare the stored role with `resolve_role` in `api/app/services/classify.py`.
- For unexpected omissions, check ingest-time `is_junk_chunk` before changing retrieval settings.
