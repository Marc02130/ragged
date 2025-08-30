# Product Requirements Document (PRD): Simple RAG App

## Overview
This PRD outlines a Retrieval-Augmented Generation (RAG) application enabling users to upload documents, vectorize them, and query via chat in threaded conversations. The app supports multiple threads per user, with secure, scoped storage and processing. It emphasizes modularity for future extensions (e.g., additional embeddings or integrations) and basic privacy/compliance (e.g., user-scoped data isolation, consent for deletions).

### Objectives
- Provide a user-friendly interface for document uploads and AI-powered chat queries.
- Ensure data security and privacy through scoped storage and authentication.
- Enable conversation history recall via vectorized chat archives.
- Support thread management, including archival on deletion for reference.

### Target Users
- Individual users (e.g., researchers, students) needing to interrogate personal documents via AI.
- Assumes basic tech literacy; no enterprise-scale features.

### Scope
- In: User auth, document uploads per thread, vectorization, RAG queries, chat history vectorization, thread deletion with archival.
- Out: Advanced analytics, multi-user collaboration, custom model training, payment integration.

## Core Features

### User Authentication and Management
- Supabase Auth for signup/login (email/password or OAuth).
- Custom table: `user_info` (user_id, preferences, metadata).
- All operations scoped to authenticated user_id.

### Thread Management
- Users create/manage multiple threads (conversations).
- Custom table: `threads` (thread_id, user_id, title, created_at, status).
- Features:
  - Create new thread.
  - List/view threads.
  - Delete thread: Prompt confirmation warning ("This will delete the OpenAI thread but archive the conversation as a TXT document for reference. Proceed?"). On confirm:
    - Delete OpenAI thread.
    - Retrieve full conversation history.
    - Vectorize and save as TXT in Supabase Storage (scoped to user).
    - Store vectors in PGVector.
    - Archive in Supabase DB for reference (e.g., in `conversations` table).

### Document Upload and Vectorization
- Secure upload to Supabase Storage: Bucket paths scoped as `/users/{user_id}/threads/{thread_id}/{doc_name}`.
- Custom table: `documents` (doc_id, thread_id, user_id, file_path, uploaded_at, vector_status).
- Process (via Edge Function):
  - Split documents using Langchain (e.g., RecursiveCharacterTextSplitter).
  - Embed chunks with OpenAI embeddings.
  - Store vectors in Supabase PGVector (table with vector column, metadata like doc_id, chunk_id).

### Chat-Based Interrogation (RAG Queries)
- OpenAI-powered RAG: For each query in a thread, retrieve relevant vectors from PGVector (similarity search), augment prompt, generate response via OpenAI.
- Thread-specific: Queries scoped to thread's documents and history.
- Save chat history in `conversations` table (conv_id, thread_id, user_id, messages array or rows with role/content/timestamp).

### Chat History Vectorization for Recall
- On each message or periodically: Vectorize recent chat history chunks (via Langchain/OpenAI).
- Store in PGVector, linked to thread_id for retrieval in future RAG queries (enables conversation recall).

## Technical Requirements

### Tech Stack
- **Frontend**: API-first React app (e.g., using Supabase JS client for auth/storage/DB interactions).
- **Backend**: Supabase Edge Functions (TypeScript) for logic like vectorization, RAG queries, deletions. Use Langchain.js for splitting/embedding.
- **Database/Storage**:
  - Supabase Postgres with PGVector extension.
  - Tables: `user_info`, `documents`, `threads`, `conversations`.
- **Integrations**:
  - OpenAI API for embeddings and completions.
  - Langchain for document processing and RAG chains.

### Architecture Principles
- Modularity: Separate concerns (e.g., vectorization as reusable Edge Function; allow swapping embedding providers via config).
- API Design: RESTful endpoints via Edge Functions (e.g., `/upload`, `/query`, `/delete-thread`).
- Error Handling: Graceful failures (e.g., retry on embedding errors; user notifications).

## Non-Functional Requirements

### Performance
- Vectorization: Asynchronous processing (queue via Edge Functions); aim for <5s per small doc.
- Queries: Response time <3s for typical RAG.

### Security and Privacy
- Data Isolation: All storage/DB queries filtered by user_id/thread_id via RLS (Row Level Security).
- Compliance: Basic GDPR-like (e.g., data deletion on user request; no sharing without consent). Log accesses; encrypt at rest via Supabase.
- Authentication: JWT tokens for all API calls.

### Scalability and Maintainability
- Start small: Handle 100 users, 10 threads/user, 50 docs/thread.
- Monitoring: Supabase logs; add basic error tracking.
- Extensions: Design hooks for future features (e.g., plugin for alternative vector DBs).

## Risks and Assumptions
- Risks: OpenAI rate limits (mitigate with caching); vector quality (test with sample docs).
- Assumptions: Users provide valid docs; Supabase handles scaling; no need for on-prem deployment.

## Next Steps
- Wireframes for React UI.
- Prototype Edge Functions for vectorization/RAG.
- Testing: Unit (functions), integration (E2E flows), security audit.