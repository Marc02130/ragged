# Technical Design Document (TDD): Simple RAG App

## 1. Introduction
### 1.1 Purpose
This Technical Design Document (TDD) provides a detailed blueprint for implementing the Simple RAG App based on the Product Requirements Document (PRD). It covers system architecture, data models, APIs, workflows, and implementation considerations. The focus is on modularity, security, and scalability for a user-centric RAG system supporting document uploads, vectorization, and threaded chat queries.

### 1.2 Scope
- Aligns with PRD: User auth, threaded document management, vectorization, RAG queries, chat history recall, and archival on deletion.
- Tech Stack: React frontend, Supabase (Auth, Storage, DB, Edge Functions), Langchain.js, OpenAI API.
- Assumptions: Single-user focus; initial scale for 100 users; no advanced features like multi-tenancy.

### 1.3 References
- PRD (Trimmed Version)
- Supabase Documentation
- Langchain.js Docs
- OpenAI API Reference

## 2. System Architecture
### 2.1 High-Level Overview
- **Frontend**: React app handles UI/UX, API calls via Supabase JS client.
- **Backend**: Serverless via Supabase Edge Functions (TypeScript) for business logic (e.g., vectorization, queries).
- **Database**: Supabase Postgres with PGVector for vector storage.
- **Storage**: Supabase Storage for documents (user/thread-scoped buckets).
- **Integrations**: OpenAI for embeddings/completions; Langchain for chunking/RAG chains.
- **Data Flow**: User → React → Edge Functions → Supabase DB/Storage → OpenAI → Response.

### 2.2 Component Diagram
```
[User] --> [React Frontend] --> [Supabase Auth] (JWT)
                  |
                  v
[Edge Functions] <--> [OpenAI API] (Embeddings/Completions)
                  |
                  v
[Supabase Storage] <--> [Supabase Postgres + PGVector]
```

### 2.3 Key Modules
- **Auth Module**: Handles login/signup; scopes all operations by user_id.
- **Thread Module**: CRUD for threads; deletion triggers archival.
- **Document Module**: Upload, vectorization (async via Edge Function).
- **Query Module**: RAG pipeline for chat queries.
- **History Module**: Periodic vectorization of chat logs.

## 3. Data Model
### 3.1 Database Schema
Based on PRD's simplified schema:

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Tables (with RLS enabled)
CREATE TABLE user_info (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id),
  preferences JSONB DEFAULT '{}'
);

CREATE TABLE threads (
  thread_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  title VARCHAR(100) NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
  doc_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  thread_id UUID NOT NULL REFERENCES threads(thread_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  file_path TEXT NOT NULL,
  vector_status VARCHAR(20) DEFAULT 'pending',
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversations (
  conv_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  thread_id UUID NOT NULL REFERENCES threads(thread_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vector_chunks (
  chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  doc_id UUID REFERENCES documents(doc_id) ON DELETE CASCADE,
  thread_id UUID NOT NULL REFERENCES threads(thread_id),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  content TEXT NOT NULL,
  embedding vector(1536),  -- For OpenAI ada-002
  metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_threads_user ON threads(user_id);
CREATE INDEX idx_documents_thread ON documents(thread_id);
CREATE INDEX idx_conversations_thread ON conversations(thread_id);
CREATE INDEX idx_vector_chunks_thread ON vector_chunks(thread_id);

-- RLS Policies (basic user scoping)
ALTER TABLE user_info ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_own_data" ON user_info FOR ALL USING (auth.uid() = user_id);

-- Similar policies for other tables...
```

### 3.2 Data Flow Examples
- **Upload**: File → Storage → Insert into `documents` → Trigger vectorization → Chunks to `vector_chunks`.
- **Query**: User input → Embed query → Similarity search in `vector_chunks` (filtered by thread_id/user_id) → Augment prompt → OpenAI response → Save to `conversations`.

## 4. API Design
### 4.1 Edge Functions (RESTful Endpoints)
- **/auth** (Handled by Supabase Auth).
- **POST /threads**: Create thread (body: {title}).
- **GET /threads**: List user threads.
- **DELETE /threads/{thread_id}**: Delete with archival (confirm in body).
- **POST /upload/{thread_id}**: Upload document (multipart form).
- **POST /query/{thread_id}**: RAG query (body: {query}).
- **POST /vectorize-chat/{thread_id}**: Manual/periodic chat vectorization.

### 4.2 Example Edge Function Skeleton (TypeScript)
```typescript
// Example: vectorize-document
export const vectorizeDocument = async (req: Request) => {
  const { docId, userId, threadId } = await req.json();
  // Auth check...
  const document = await loadFromStorage(filePath);
  const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000, chunkOverlap: 200 });
  const chunks = await splitter.splitDocuments([document]);
  const embeddings = await openAI.embeddings.create({ model: 'text-embedding-ada-002', input: chunks.map(c => c.pageContent) });
  // Insert to vector_chunks...
  return new Response(JSON.stringify({ status: 'ready' }));
};
```

## 5. Workflows
### 5.1 Document Upload and Vectorization
1. User uploads file via React.
2. Edge Function validates and stores in scoped bucket.
3. Async trigger: Split → Embed → Store vectors.
4. Update `documents.vector_status`.

### 5.2 RAG Query
1. Embed user query.
2. PGVector similarity search (cosine, threshold 0.7, top 10).
3. Fetch recent chat history from `conversations`.
4. Augment prompt with context/history.
5. OpenAI completion.
6. Save messages to `conversations`.

### 5.3 Thread Deletion
1. Confirm via UI.
2. Retrieve conversations.
3. Export to TXT, vectorize, store in archives bucket and `vector_chunks`.
4. Soft-delete thread (status = 'archived').

### 5.4 Chat History Vectorization
- Trigger: Every 5 messages or on inactivity.
- Chunk messages → Embed → Store in `vector_chunks` with type='chat'.

## 6. Non-Functional Considerations
### 6.1 Security
- RLS for data isolation.
- JWT auth for all APIs.
- Scoped storage paths.

### 6.2 Performance
- Async processing for vectorization.
- Caching for frequent queries (optional Redis).
- Target: <3s query response.

### 6.3 Error Handling
- Retry on OpenAI failures.
- User notifications for uploads/queries.

### 6.4 Scalability
- Serverless Edge Functions auto-scale.
- PGVector indexes for fast searches.

## 7. Implementation Plan
- **Phase 1**: Setup Supabase, auth, basic DB schema.
- **Phase 2**: Implement Edge Functions for core workflows.
- **Phase 3**: Build React UI and integrate APIs.
- **Phase 4**: Testing and deployment.

## 8. Risks and Mitigations
- OpenAI costs/limits: Implement quotas and caching.
- Vector accuracy: Tune chunk sizes/thresholds.
