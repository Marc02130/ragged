# RAGged Diagrams

These Mermaid diagrams describe the current FastAPI, Webpack React, PostgreSQL/pgvector, and Docker Compose application.

| File | Scope |
| --- | --- |
| [upload-to-query-flow.md](upload-to-query-flow.md) | Sequential upload, ingest, rewrite, retrieval, and answer generation |
| [multi-thread-architecture.md](multi-thread-architecture.md) | User/thread isolation and same-thread retrieval |
| [database-schema.md](database-schema.md) | Current SQLAlchemy/Alembic entities and relationships |
| [thread-deletion-flow.md](thread-deletion-flow.md) | Archive, restore, and permanent deletion |

GitHub renders Mermaid blocks directly. When implementation changes, verify these diagrams against `api/app/models.py`, `api/app/routers/`, and `api/app/services/` rather than historical Supabase design documents.
