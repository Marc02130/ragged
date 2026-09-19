# Database Schema

The authoritative definitions are `api/app/models.py` and `api/alembic/versions/`.

```mermaid
erDiagram
    USERS ||--o{ THREADS : owns
    USERS ||--o| USER_LLM_SETTINGS : configures
    USERS ||--o{ DOCUMENTS : uploads
    USERS ||--o{ CONVERSATIONS : writes
    USERS ||--o{ VECTOR_CHUNKS : owns

    THREADS ||--o{ DOCUMENTS : contains
    THREADS ||--o{ CONVERSATIONS : contains
    THREADS ||--o{ VECTOR_CHUNKS : scopes
    DOCUMENTS ||--o{ VECTOR_CHUNKS : produces

    USERS {
        uuid id PK
        string email UK
        string password_hash
        timestamptz created_at
    }
    THREADS {
        uuid id PK
        uuid user_id FK
        string title
        string status
        int document_count
        timestamptz last_activity_at
        timestamptz created_at
        timestamptz updated_at
    }
    DOCUMENTS {
        uuid id PK
        uuid thread_id FK
        uuid user_id FK
        string file_path
        string file_name
        bigint file_size
        string file_type
        string title
        text content
        string status
        string embedding_model
        int chunk_count
        text error_message
        timestamptz updated_at
    }
    VECTOR_CHUNKS {
        uuid id PK
        uuid document_id FK
        uuid thread_id FK
        uuid user_id FK
        text content
        vector_384 embedding
        string embedding_model
        int chunk_index
        jsonb metadata
        timestamptz created_at
    }
    CONVERSATIONS {
        uuid id PK
        uuid thread_id FK
        uuid user_id FK
        string role
        text content
        jsonb metadata
        timestamptz created_at
    }
    USER_LLM_SETTINGS {
        uuid user_id PK_FK
        text openai_key_enc
        text xai_key_enc
        text anthropic_key_enc
        string chat_provider
        timestamptz created_at
        timestamptz updated_at
    }
```

Thread deletion cascades through documents, conversations, and chunks. Document deletion cascades to its chunks. Users are authenticated by application code; there is no Supabase `auth.users` table or RLS policy layer.
