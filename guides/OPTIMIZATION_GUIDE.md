# Optimization Guide

This guide documents the current limits and tuning points for document ingest and retrieval. Values come from `api/app/config.py`.

## Upload and ingest limits

| Setting | Default |
| --- | ---: |
| Maximum file size | 10 MiB |
| Maximum multipart request body | 55 MiB |
| Maximum files per thread | 20 |
| Maximum ready/processing bytes per thread | 50 MiB |
| Maximum ready/processing bytes per user | 1 GiB |
| Maximum extracted characters per document | 1,000,000 |
| Maximum retained chunks per document | 1,000 |
| Chunk size / overlap | 1000 / 200 characters |

FastAPI reads and validates the request, then ingests files one at a time. The React client also uploads selected files sequentially, one request per file. This reduces concurrent model and memory pressure but means a large selection can take longer.

Text is split at paragraph, line, sentence, and word boundaries while carrying the nearest detected heading. Citation and boilerplate junk is removed before embedding.

## Embedding batches

`api/app/services/embeddings.py` sends retained text to local FastEmbed in batches of 32. The embedding model is loaded lazily once per API worker. Compose starts two workers, so each worker can hold its own model instance.

Changing the embedding model or dimension requires compatible database vectors and re-embedding existing documents. Retrieval filters rows by the configured model name, so changing only the environment setting makes old chunks unsearchable.

`EMBEDDING_PROVIDER=stub` returns deterministic placeholder vectors and is intended only for tests.

## Retrieval tuning

| Setting | Default | Effect |
| --- | ---: | --- |
| `WIDE_VECTOR_RESULTS` | 32 | Nearest candidates per query-plan text |
| `MAX_VECTOR_RESULTS` | 8 | Maximum sources sent to answer generation |
| `RELATIVE_SCORE_MARGIN` | 0.15 | Keep hits this close to the best raw cosine |

Increasing the wide pool improves recall but multiplies work across the original, rewrite, and two HyDE embeddings. Increasing final results increases prompt size and optional grading work.

`SIMILARITY_THRESHOLD` is currently not applied by `retrieve_hits`; tune the relative margin instead.

## PostgreSQL

The SQLAlchemy pool defaults to five connections with five overflow connections per API process. Retrieval queries are scoped by `user_id`, `thread_id`, and `embedding_model`; preserve indexes supporting those filters when changing the schema.

Measure with the real document corpus before adding an approximate vector index. The checked-in migrations define the supported schema; do not apply standalone SQL copied from old Supabase design documents.

## Practical diagnosis

- High API memory: inspect document sizes/chunk counts and remember there are two model-holding workers.
- Slow uploads: separate extraction time from embedding time and check whether model initialization is occurring.
- Too many weak sources: reduce `RELATIVE_SCORE_MARGIN` or `MAX_VECTOR_RESULTS`.
- Too few sources: inspect ingest junk filtering before widening retrieval.
- Old documents disappear after a model change: restore the prior model setting or re-ingest them with a deliberate migration plan.
