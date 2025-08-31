# Multi-Thread Architecture Diagram

This diagram shows how multiple threads are managed per user, including thread isolation, cross-thread search capabilities, and user-scoped data management.

```mermaid
flowchart TD
    %% User Authentication
    USER[Authenticated User<br/>user_id: abc-123] --> AUTH[Supabase Auth<br/>JWT Token]
    
    %% User Profile
    AUTH --> USER_PROFILE[User Profile<br/>user_profiles table]
    
    %% Multiple Threads
    USER --> THREAD_1[Thread 1<br/>"Research Paper"<br/>thread_id: t1-456]
    USER --> THREAD_2[Thread 2<br/>"Meeting Notes"<br/>thread_id: t2-789]
    USER --> THREAD_3[Thread 3<br/>"Project Docs"<br/>thread_id: t3-012]
    USER --> THREAD_N[Thread N<br/>...<br/>thread_id: tN-xxx]
    
    %% Thread Isolation
    subgraph "Thread 1 - Research Paper"
        T1_DOCS[Documents<br/>- paper1.pdf<br/>- paper2.pdf]
        T1_CONV[Conversations<br/>- Q: "What are the main findings?"<br/>- A: "The research shows..."]
        T1_VECTORS[Vector Chunks<br/>- paper1 chunks<br/>- paper2 chunks]
    end
    
    subgraph "Thread 2 - Meeting Notes"
        T2_DOCS[Documents<br/>- meeting1.docx<br/>- notes.txt]
        T2_CONV[Conversations<br/>- Q: "What was discussed?"<br/>- A: "The meeting covered..."]
        T2_VECTORS[Vector Chunks<br/>- meeting1 chunks<br/>- notes chunks]
    end
    
    subgraph "Thread 3 - Project Docs"
        T3_DOCS[Documents<br/>- spec.pdf<br/>- requirements.docx]
        T3_CONV[Conversations<br/>- Q: "What are the requirements?"<br/>- A: "The project requires..."]
        T3_VECTORS[Vector Chunks<br/>- spec chunks<br/>- requirements chunks]
    end
    
    %% Connect threads to their data
    THREAD_1 --> T1_DOCS
    THREAD_1 --> T1_CONV
    THREAD_1 --> T1_VECTORS
    
    THREAD_2 --> T2_DOCS
    THREAD_2 --> T2_CONV
    THREAD_2 --> T2_VECTORS
    
    THREAD_3 --> T3_DOCS
    THREAD_3 --> T3_CONV
    THREAD_3 --> T3_VECTORS
    
    %% Cross-Thread Search
    QUERY[User Query<br/>"Find information about..."<br/>from Thread 1] --> CROSS_SEARCH[Cross-Thread Search<br/>Edge Function: rag-query]
    
    CROSS_SEARCH --> SEARCH_T1[Search Thread 1<br/>Current thread]
    CROSS_SEARCH --> SEARCH_T2[Search Thread 2<br/>Other threads]
    CROSS_SEARCH --> SEARCH_T3[Search Thread 3<br/>Other threads]
    CROSS_SEARCH --> SEARCH_ARCHIVES[Search Archives<br/>Deleted threads]
    
    %% Search Results Aggregation
    SEARCH_T1 --> AGGREGATE[Aggregate Results<br/>Rank by relevance]
    SEARCH_T2 --> AGGREGATE
    SEARCH_T3 --> AGGREGATE
    SEARCH_ARCHIVES --> AGGREGATE
    
    AGGREGATE --> RAG_RESPONSE[RAG Response<br/>With cross-thread context]
    
    %% Database Tables with User Scoping
    subgraph "Database Tables (User-Scoped)"
        DB_THREADS[(threads<br/>user_id = abc-123)]
        DB_DOCS[(documents<br/>user_id = abc-123)]
        DB_CONV[(conversations<br/>user_id = abc-123)]
        DB_VECTORS[(vector_chunks<br/>user_id = abc-123)]
        DB_ARCHIVES[(vector_chunks<br/>source_type='thread_archive'<br/>user_id = abc-123)]
    end
    
    %% RLS Policies
    subgraph "Row Level Security (RLS)"
        RLS_THREADS[threads RLS:<br/>auth.uid() = user_id]
        RLS_DOCS[documents RLS:<br/>auth.uid() = user_id]
        RLS_CONV[conversations RLS:<br/>auth.uid() = user_id]
        RLS_VECTORS[vector_chunks RLS:<br/>auth.uid() = user_id]
    end
    
    %% Connect to database
    THREAD_1 --> DB_THREADS
    THREAD_2 --> DB_THREADS
    THREAD_3 --> DB_THREADS
    
    T1_DOCS --> DB_DOCS
    T2_DOCS --> DB_DOCS
    T3_DOCS --> DB_DOCS
    
    T1_CONV --> DB_CONV
    T2_CONV --> DB_CONV
    T3_CONV --> DB_CONV
    
    T1_VECTORS --> DB_VECTORS
    T2_VECTORS --> DB_VECTORS
    T3_VECTORS --> DB_VECTORS
    
    SEARCH_ARCHIVES --> DB_ARCHIVES
    
    %% Thread Management Operations
    subgraph "Thread Operations"
        CREATE_THREAD[Create Thread<br/>New conversation topic]
        SWITCH_THREAD[Switch Thread<br/>Change active thread]
        DELETE_THREAD[Delete Thread<br/>Archive & cleanup]
        SEARCH_THREADS[Search Threads<br/>Find relevant threads]
    end
    
    USER --> CREATE_THREAD
    USER --> SWITCH_THREAD
    USER --> DELETE_THREAD
    USER --> SEARCH_THREADS
    
    %% Thread Deletion Flow
    DELETE_THREAD --> ARCHIVE_PROCESS[Archive Process<br/>Create vectorized archive]
    ARCHIVE_PROCESS --> STORE_ARCHIVE[Store Archive<br/>vector_chunks table<br/>source_type='thread_archive']
    STORE_ARCHIVE --> DB_ARCHIVES
    
    %% User Isolation Examples
    subgraph "User Isolation Examples"
        USER_A[User A<br/>user_id: abc-123] --> THREADS_A[User A's Threads<br/>- Research Paper<br/>- Meeting Notes]
        USER_B[User B<br/>user_id: def-456] --> THREADS_B[User B's Threads<br/>- Project Docs<br/>- Personal Notes]
    end
    
    %% Cross-Thread Search Configuration
    subgraph "Cross-Thread Search Config"
        SEARCH_CONFIG[Search Configuration<br/>- maxThreadsSearch: 5<br/>- currentThreadPriority: true<br/>- similarityThreshold: 0.8]
    end
    
    CROSS_SEARCH --> SEARCH_CONFIG
    
    %% Styling
    classDef user fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef thread fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef database fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef rls fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef operation fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef search fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef archive fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    
    class USER,USER_A,USER_B user
    class THREAD_1,THREAD_2,THREAD_3,THREAD_N,THREADS_A,THREADS_B thread
    class DB_THREADS,DB_DOCS,DB_CONV,DB_VECTORS,DB_ARCHIVES database
    class RLS_THREADS,RLS_DOCS,RLS_CONV,RLS_VECTORS rls
    class CREATE_THREAD,SWITCH_THREAD,DELETE_THREAD,SEARCH_THREADS operation
    class QUERY,CROSS_SEARCH,SEARCH_T1,SEARCH_T2,SEARCH_T3,AGGREGATE,RAG_RESPONSE,SEARCH_CONFIG search
    class ARCHIVE_PROCESS,STORE_ARCHIVE,SEARCH_ARCHIVES archive
```

## Architecture Details

### 1. User Isolation & Multi-Tenancy

#### User Scoping
- **Authentication**: Each user has unique `user_id` from Supabase Auth
- **Data Isolation**: All data scoped to `user_id` in database tables
- **RLS Policies**: Row Level Security ensures users only access their own data

#### Thread Independence
- **Multiple Threads**: Users can create unlimited threads
- **Thread Isolation**: Each thread is completely independent
- **No Cross-User Access**: Users cannot access other users' threads

### 2. Thread Structure

#### Thread Components
Each thread contains:
- **Thread Metadata**: Title, creation date, last activity
- **Documents**: Uploaded files (PDF, DOCX, TXT, RTF)
- **Conversations**: Chat history (user questions, AI responses)
- **Vector Chunks**: Document embeddings for RAG search

#### Thread Example
```
Thread: "Research Paper Analysis"
├── Documents
│   ├── paper1.pdf (vectorized)
│   └── paper2.pdf (vectorized)
├── Conversations
│   ├── Q: "What are the main findings?"
│   ├── A: "The research shows..."
│   ├── Q: "How does this relate to previous work?"
│   └── A: "This builds upon..."
└── Vector Chunks
    ├── paper1_chunk_1 (embedding)
    ├── paper1_chunk_2 (embedding)
    ├── paper2_chunk_1 (embedding)
    └── paper2_chunk_2 (embedding)
```

### 3. Cross-Thread Search

#### Search Configuration
```javascript
const searchConfig = {
  maxThreadsSearch: 5,        // Maximum threads to search
  currentThreadPriority: true, // Prioritize current thread
  similarityThreshold: 0.8,   // Higher threshold for cross-thread
  includeArchives: true       // Include deleted thread archives
}
```

#### Search Process
1. **Query Embedding**: Generate embedding for user query
2. **Thread Selection**: Select relevant threads to search
3. **Vector Search**: Search across selected threads
4. **Result Aggregation**: Combine and rank results
5. **Context Building**: Build RAG context from multiple threads

#### Cross-Thread Search Example
```sql
-- Search across multiple threads
SELECT 
  vc.content,
  vc.metadata,
  vc.similarity,
  t.title as thread_title
FROM vector_chunks vc
JOIN documents d ON vc.document_id = d.id
JOIN threads t ON d.thread_id = t.id
WHERE vc.user_id = $1
  AND t.id = ANY($2) -- Array of thread IDs
  AND vc.similarity > $3
ORDER BY vc.similarity DESC
LIMIT 10;
```

### 4. Database Schema with User Scoping

#### Tables with User Isolation
```sql
-- All tables include user_id for scoping
CREATE TABLE threads (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id), -- User scoping
  title TEXT NOT NULL,
  status TEXT DEFAULT 'active'
);

CREATE TABLE documents (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id), -- User scoping
  thread_id UUID REFERENCES threads(id),
  title TEXT NOT NULL
);

CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  thread_id UUID REFERENCES threads(id),
  user_id UUID REFERENCES auth.users(id), -- User scoping
  role TEXT NOT NULL,
  content TEXT NOT NULL
);

CREATE TABLE vector_chunks (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id),
  user_id UUID REFERENCES auth.users(id), -- User scoping
  content TEXT NOT NULL,
  embedding VECTOR(1536)
);
```

### 5. Row Level Security (RLS)

#### RLS Policies
```sql
-- Users can only access their own threads
CREATE POLICY "Users can view own threads" ON threads
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only access their own documents
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only access conversations in their own threads
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        )
    );

-- Users can only access their own vector chunks
CREATE POLICY "Users can view own vector chunks" ON vector_chunks
    FOR SELECT USING (auth.uid() = user_id);
```

### 6. Thread Management Operations

#### Create Thread
```javascript
const createThread = async (userId, title) => {
  const { data, error } = await supabase
    .from('threads')
    .insert({
      user_id: userId,
      title: title,
      status: 'active'
    })
    .select()
    .single()
  
  return data
}
```

#### Switch Thread
```javascript
const switchThread = async (userId, threadId) => {
  // Verify user owns the thread
  const { data, error } = await supabase
    .from('threads')
    .select('*')
    .eq('id', threadId)
    .eq('user_id', userId)
    .single()
  
  if (error) throw new Error('Thread not found or access denied')
  return data
}
```

#### Search Threads
```javascript
const searchThreads = async (userId, query) => {
  // Search thread titles and content
  const { data, error } = await supabase
    .from('threads')
    .select(`
      id,
      title,
      conversations(content),
      documents(title)
    `)
    .eq('user_id', userId)
    .textSearch('title', query)
  
  return data
}
```

### 7. Archive Integration

#### Thread Archive Storage
```sql
-- Archive vectors are stored with special metadata
INSERT INTO vector_chunks (
  user_id,
  content,
  embedding,
  metadata
) VALUES (
  $1, -- user_id
  $2, -- archive content
  $3, -- archive embedding
  '{
    "source_type": "thread_archive",
    "archived_from": "thread_id",
    "archived_at": "timestamp",
    "conversation_count": 10,
    "document_count": 3
  }'::jsonb
);
```

#### Archive Search
```javascript
const searchIncludingArchives = async (userId, query) => {
  const { data, error } = await supabase
    .rpc('match_documents_with_archives', {
      query_embedding: queryEmbedding,
      match_threshold: 0.7,
      match_count: 10,
      p_user_id: userId
    })
  
  return data
}
```

### 8. Performance Considerations

#### Thread-Specific Optimizations
- **Indexing**: Optimized indexes for user_id + thread_id queries
- **Caching**: Thread-specific caching for frequently accessed data
- **Pagination**: Efficient pagination for large thread lists

#### Cross-Thread Search Optimization
- **Limited Scope**: Search limited number of threads
- **Priority Weighting**: Current thread gets higher priority
- **Archive Filtering**: Separate handling for archive vectors

### 9. Security Features

#### User Isolation
- **Complete Separation**: No data leakage between users
- **RLS Enforcement**: Database-level security policies
- **Service Role**: Edge Functions use service role for operations

#### Thread Security
- **Ownership Verification**: All operations verify thread ownership
- **Access Control**: Users can only access their own threads
- **Audit Trail**: Track thread creation, modification, deletion

### 10. Scalability Considerations

#### Multi-Thread Scaling
- **Unlimited Threads**: Users can create unlimited threads
- **Efficient Storage**: Optimized storage for thread metadata
- **Performance Monitoring**: Track thread performance metrics

#### Cross-Thread Search Scaling
- **Configurable Limits**: Adjustable search scope
- **Result Ranking**: Intelligent result aggregation
- **Caching Strategy**: Cache cross-thread search results 