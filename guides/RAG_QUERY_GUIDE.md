# RAG Query Guide

RAGged answers questions only from ready documents in the selected thread. The query endpoint is:

```http
POST /api/threads/{thread_id}/messages
Content-Type: application/json

{"content":"What evidence supports the main hypothesis?"}
```

Authentication uses the `ragged_session` HTTP-only cookie. The response contains the saved user and assistant messages:

```json
{
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "What evidence supports the main hypothesis?",
    "created_at": "2026-09-19T20:00:00Z",
    "sources": []
  },
  "assistant_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "Answer grounded in the uploaded documents.",
    "created_at": "2026-09-19T20:00:01Z",
    "sources": [
      {
        "chunk_id": "uuid",
        "document_id": "uuid",
        "file_name": "paper.pdf",
        "content": "Retrieved chunk text",
        "similarity": 0.73
      }
    ]
  }
}
```

`content` must contain 1–8000 characters. The authenticated user must own the thread; an unknown or unowned thread returns `404`.

## Query processing

The implemented path is `api/app/services/rag.py`:

1. Load up to eight recent unique user questions from this thread.
2. Ask the configured chat provider for a query plan. The rewrite prompt includes the thread title, up to 20 ready-document file names, and up to 40 stored headings.
3. The plan can contain:
   - a standalone rewrite in the corpus vocabulary;
   - up to eight aliases;
   - up to two hypothetical passages: a news lede and a plain personal note.
4. Embed the original query with its two most recent unique questions, the rewrite, and the HyDE passages. Empty or duplicate texts are omitted.
5. Retrieve a wide nearest-neighbor pool for each embedding and add lexical candidates matching query/rewrite terms.
6. Fuse the rankings with reciprocal rank fusion (RRF).
7. Keep results within `RELATIVE_SCORE_MARGIN` of the best cosine score, then cap at `MAX_VECTOR_RESULTS`.
8. Expand a short title-like hit with adjacent chunks and optionally ask the chat provider to reject remaining bibliography/title-only results.
9. Generate an answer from the retained sources and save both messages.

Rewrite is best effort. Stub embeddings, a missing chat key, malformed rewrite JSON, or a rewrite-provider error produces an empty plan; retrieval still uses the original query.

## Providers and embeddings

- Document and query embeddings are local `sentence-transformers/all-MiniLM-L6-v2` vectors by default (384 dimensions).
- `EMBEDDING_PROVIDER=stub` is for tests.
- Answer generation and query rewriting use the user-selected OpenAI, xAI, or Anthropic provider.
- Users manage provider keys under **API keys**. Operator environment keys are fallbacks.
- Model, temperature, result count, and retrieval strategy are server settings, not request options.

## Scope and conversation history

Retrieval always filters by both authenticated user and current thread. There is no cross-thread retrieval and chat messages are not embedded. Earlier user questions only help expand follow-up queries.

## Source behavior

Sources are stored with assistant messages and returned by both message endpoints. If the generated content exactly matches the canned refusal, sources are not stored. The browser displays source file names and chunk content.

## Failures and no results

When retrieval returns no chunks, RAGged stores the question and a canned refusal with an empty source list. It does not answer from general knowledge and does not vectorize the conversation. See [NO_RESULTS_HANDLING_GUIDE.md](NO_RESULTS_HANDLING_GUIDE.md).

A configured-provider/key problem during final answer generation returns `400`. Provider transport errors other than missing-key errors are not converted into a custom API response.

## Implementation references

- Route and response shape: `api/app/routers/messages.py`, `api/app/schemas.py`
- Rewrite and corpus conditioning: `api/app/services/rewrite.py`
- Retrieval, RRF, relative cutoff, grading: `api/app/services/rag.py`
- Prompts and refusal: `api/app/prompts.py`
- Provider calls: `api/app/services/chat.py`
