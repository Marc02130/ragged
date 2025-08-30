# Trimmed Product Requirements Document (PRD): Simple RAG App

## Overview
This PRD outlines a Retrieval-Augmented Generation (RAG) application enabling users to upload documents, vectorize them, and query via chat in threaded conversations. The app supports multiple threads per user, with secure, scoped storage and processing. It emphasizes modularity for future extensions and basic privacy/compliance (e.g., user-scoped data isolation, consent for deletions).

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
  - Create new thread with title.
  - List/view threads.
  - Delete thread: Prompt confirmation warning. On confirm:
    - Delete OpenAI thread.
    - Retrieve full conversation history.
    - Vectorize and save as TXT in Supabase Storage (scoped to user).
    - Store vectors in PGVector.
    - Archive in Supabase DB for reference (e.g., in `conversations` table).

### Document Upload and Vectorization
- Secure upload to Supabase Storage: Bucket paths scoped as `/users/{user_id}/threads/{thread_id}/{doc_name}`.
- Custom table: `documents` (doc_id, thread_id, user_id, file_path, uploaded_at, vector_status).
- Process (via Edge Function):
  - Split documents using Langchain (RecursiveCharacterTextSplitter).
  - Embed chunks with OpenAI embeddings (`text-embedding-ada-002`).
  - Store vectors in Supabase PGVector with metadata (doc_id, chunk_id).

### Chat-Based Interrogation (RAG Queries)
- OpenAI-powered RAG: Retrieve relevant vectors from PGVector (similarity search), augment prompt, generate response via OpenAI (GPT-4 or GPT-3.5-turbo).
- Thread-specific: Queries scoped to thread's documents and history.
- Save chat history in `conversations` table (conv_id, thread_id, user_id, role, content, timestamp).

### Chat History Vectorization for Recall
- Periodically vectorize chat history chunks (via Langchain/OpenAI).
- Store in PGVector, linked to thread_id for retrieval in future RAG queries.

## Technical Requirements

### Tech Stack
- **Frontend**: API-first React app using Supabase JS client and tailwind.
- **Backend**: Supabase Edge Functions (TypeScript) for logic like vectorization, RAG queries, deletions. Use Langchain.js for processing.
- **Database/Storage**:
  - Supabase Postgres with PGVector extension.
  - Tables: `user_info`, `documents`, `threads`, `conversations`.
- **Integrations**:
  - OpenAI API for embeddings and completions.
  - Langchain for document processing and RAG chains.

### Database Schema (Simplified)
```sql
CREATE TABLE user_info (
  user_id UUID PRIMARY KEY,
  preferences JSONB
);

CREATE TABLE threads (
  thread_id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  title VARCHAR(100) NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE documents (
  doc_id UUID PRIMARY KEY,
  thread_id UUID NOT NULL,
  user_id UUID NOT NULL,
  file_path TEXT NOT NULL,
  vector_status VARCHAR(20) DEFAULT 'pending',
  uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversations (
  conv_id UUID PRIMARY KEY,
  thread_id UUID NOT NULL,
  user_id UUID NOT NULL,
  role VARCHAR(10) NOT NULL,
  content TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE vector_chunks (
  chunk_id UUID PRIMARY KEY,
  doc_id UUID,
  thread_id UUID NOT NULL,
  user_id UUID NOT NULL,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB
);
```
- Enable RLS on all tables to scope by user_id.

### Architecture Principles
- Modularity: Separate concerns (e.g., vectorization as reusable Edge Function).
- API Design: RESTful endpoints via Edge Functions (e.g., `/upload`, `/query`, `/delete-thread`).
- Error Handling: Graceful failures with user notifications.

## Non-Functional Requirements

### Performance
- Vectorization: Asynchronous; aim for <5s per small doc.
- Queries: Response time <3s.

### Security and Privacy
- Data Isolation: RLS for user-scoped access.
- Compliance: Basic (e.g., data deletion on request; no sharing without consent).
- Authentication: JWT for API calls.

### Scalability and Maintainability
- Handle 100 users initially.
- Monitoring: Use Supabase logs.

## Risks and Assumptions
- Risks: OpenAI rate limits (mitigate with caching); vector quality (test with samples).
- Assumptions: Users provide valid docs; Supabase handles scaling.

## Next Steps
- Prototype Edge Functions for vectorization/RAG.
- Build React UI for core flows.
- Testing: Unit and integration for key features.