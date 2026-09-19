# No-Results Handling Guide

RAGged refuses to answer when retrieval produces no usable document chunks. It does not fall back to general model knowledge.

## Behavior

`POST /api/threads/{thread_id}/messages` always saves the user's valid question. If both retrieval attempts return no hits, it also saves an assistant message containing `CANNED_REFUSAL` from `api/app/prompts.py`.

Both messages have empty `sources` arrays. The endpoint still returns `200` with the normal `CreateMessageResponse`; no special `fallbackGenerated` field exists.

The first retrieval attempt includes the original query (expanded with recent questions), rewrite, and HyDE texts. If it has no hits, a second attempt omits the original/expanded text and retries available rewrite/HyDE texts. If query rewriting produced no alternate texts, the retry is empty and refusal follows.

## What does not happen

- No general-knowledge answer is generated.
- The refusal path does not call the final answer model.
- User or assistant messages are not embedded.
- No conversation vector is added to `vector_chunks`.
- No cross-thread or archived-thread search is attempted.
- No fallback-specific status or performance telemetry is returned.

This behavior keeps answers grounded in uploaded documents and prevents unsupported answers from appearing authoritative.

## Client handling

Clients should use the normal response shape and treat an assistant message with no sources as uncited. The current web client renders the assistant text and only shows the sources section when sources exist.

Do not infer “no results” solely from HTTP status: successful refusals use
`200`. A query that has retrieved sources but no usable key also returns `200`;
its assistant content is the placeholder `Answer based on SOURCES.` and its
sources remain attached. That is not a no-results response.

## Diagnosing unexpected refusals

1. List documents with `GET /api/threads/{thread_id}/documents`.
2. Confirm at least one document is `ready` with `chunk_count > 0`.
3. Confirm the question is sent to the document's thread.
4. Check that stored chunks use the current embedding model.
5. Review ingest filtering and retrieval filtering in:
   - `api/app/services/classify.py`
   - `api/app/services/rag.py`
6. If rewrite should help, confirm a chat provider key is configured. Rewrite failures degrade to original-query retrieval without surfacing a separate error.
