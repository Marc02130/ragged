# RAGged API Documentation

Comprehensive API reference for the RAGged application, including Edge Functions, database operations, and integration examples.

## Table of Contents

- [Edge Functions](#edge-functions)
- [Database API](#database-api)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)
- [Examples](#examples)

---

## Edge Functions

### 1. Vectorize Function

**Endpoint**: `POST /functions/v1/vectorize`

Processes and vectorizes uploaded documents using Langchain.js and OpenAI embeddings.

#### Request

```typescript
interface VectorizeRequest {
  documentId: string
  userId: string
  content: string
  fileName: string
  fileType: string
  maxChunks?: number
  chunkSize?: number
  chunkOverlap?: number
}
```

#### Response

```typescript
interface VectorizeResponse {
  success: boolean
  vectorCount: number
  processedChunks: number
  totalChunks: number
  message?: string
  error?: string
}
```

#### Example

```javascript
const response = await supabase.functions.invoke('vectorize', {
  body: {
    documentId: '550e8400-e29b-41d4-a716-446655440000',
    userId: 'user-uuid',
    content: 'Document content here...',
    fileName: 'research-paper.pdf',
    fileType: 'application/pdf',
    maxChunks: 100,
    chunkSize: 1000,
    chunkOverlap: 200
  }
})

if (response.data.success) {
  console.log(`Processed ${response.data.vectorCount} vectors`)
} else {
  console.error('Vectorization failed:', response.data.error)
}
```

#### Configuration

- **Default Chunk Size**: 1000 tokens
- **Default Chunk Overlap**: 200 tokens
- **Max Chunks**: 100 (configurable)
- **Embedding Model**: OpenAI text-embedding-ada-002
- **Vector Dimension**: 1536

---

### 2. RAG Query Function

**Endpoint**: `POST /functions/v1/rag-query`

Performs intelligent document queries using Retrieval-Augmented Generation.

#### Request

```typescript
interface RAGQueryRequest {
  threadId: string
  userId: string
  query: string
  maxResults?: number
  includeChatHistory?: boolean
  temperature?: number
  model?: string
  includeThreadContext?: boolean
  searchStrategy?: 'hybrid' | 'semantic' | 'keyword'
  responseFormat?: 'text' | 'structured'
  // Cross-thread search options
  crossThreadSearch?: boolean
  maxThreadsSearch?: number
  currentThreadPriority?: boolean
  // Retrieval filtering
  topKPerThread?: number
  similarityThreshold?: number
}
```

#### Response

```typescript
interface RAGQueryResponse {
  success: boolean
  response?: string
  sources?: Array<{
    content: string
    metadata: Record<string, any>
    similarity: number
    sourceType: 'document' | 'chat_history' | 'thread_archive'
    threadId?: string
    documentId?: string
  }>
  conversationId?: string
  threadContext?: {
    threadId: string
    threadTitle: string
    conversationCount: number
    lastActivity: string
  }
  performance?: {
    searchTime: number
    generationTime: number
    totalTime: number
    tokensUsed: number
  }
  fallbackGenerated?: boolean
  error?: string
}
```

#### Example

```javascript
const response = await supabase.functions.invoke('rag-query', {
  body: {
    threadId: 'thread-uuid',
    userId: 'user-uuid',
    query: 'What are the main findings in the research?',
    includeChatHistory: true,
    crossThreadSearch: true,
    maxThreadsSearch: 3,
    temperature: 0.7,
    model: 'gpt-4',
    maxResults: 8
  }
})

if (response.data.success) {
  console.log('AI Response:', response.data.response)
  console.log('Sources:', response.data.sources)
  console.log('Performance:', response.data.performance)
} else {
  console.error('Query failed:', response.data.error)
}
```

#### Configuration

- **Default Model**: GPT-4
- **Default Temperature**: 0.7
- **Max Results**: 8
- **Similarity Threshold**: 0.7
- **Max Threads Search**: 5
- **Top K Per Thread**: 3

---

### 3. Delete Thread Function

**Endpoint**: `POST /functions/v1/delete-thread`

Archives and deletes threads with confirmation and vectorized conversation preservation.

#### Request

```typescript
interface DeleteThreadRequest {
  threadId: string
  userId: string
  confirmDeletion: boolean
  archiveConversations?: boolean
  preserveVectors?: boolean
}
```

#### Response

```typescript
interface DeleteThreadResponse {
  success: boolean
  message?: string
  archivedConversations?: number
  archivedVectors?: number
  error?: string
}
```

#### Example

```javascript
const response = await supabase.functions.invoke('delete-thread', {
  body: {
    threadId: 'thread-uuid',
    userId: 'user-uuid',
    confirmDeletion: true,
    archiveConversations: true,
    preserveVectors: true
  }
})

if (response.data.success) {
  console.log(`Archived ${response.data.archivedConversations} conversations`)
  console.log(`Preserved ${response.data.archivedVectors} vectors`)
} else {
  console.error('Deletion failed:', response.data.error)
}
```

#### Process

1. **Confirmation Check**: Verifies `confirmDeletion` is `true`
2. **Thread Validation**: Ensures thread exists and belongs to user
3. **Conversation Archive**: Creates vectorized archive of all conversations
4. **Vector Preservation**: Stores archive as vector chunks for future retrieval
5. **Cascade Deletion**: Removes thread and all associated data
6. **Cleanup**: Removes orphaned documents and vectors

---

## Database API

### Authentication

All database operations require authentication:

```javascript
// Initialize Supabase client
const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
)

// Get current user
const { data: { user }, error } = await supabase.auth.getUser()
if (!user) throw new Error('Authentication required')
```

### Thread Management

#### Create Thread

```javascript
const { data: thread, error } = await supabase
  .from('threads')
  .insert({
    title: 'Research Discussion',
    user_id: userId,
    status: 'active'
  })
  .select()
  .single()

if (error) throw error
console.log('Created thread:', thread.id)
```

#### Get User Threads

```javascript
const { data: threads, error } = await supabase
  .from('threads')
  .select(`
    id,
    title,
    status,
    created_at,
    updated_at,
    last_activity_at,
    conversations(count)
  `)
  .eq('user_id', userId)
  .order('updated_at', { ascending: false })

if (error) throw error
console.log('User threads:', threads)
```

#### Update Thread

```javascript
const { data: thread, error } = await supabase
  .from('threads')
  .update({
    title: 'Updated Title',
    last_activity_at: new Date().toISOString()
  })
  .eq('id', threadId)
  .eq('user_id', userId)
  .select()
  .single()

if (error) throw error
```

#### Delete Thread

```javascript
// Use Edge Function for proper archival
const response = await supabase.functions.invoke('delete-thread', {
  body: {
    threadId: threadId,
    userId: userId,
    confirmDeletion: true
  }
})
```

### Document Management

#### Upload Document

```javascript
// 1. Create document record
const { data: document, error } = await supabase
  .from('documents')
  .insert({
    title: 'Research Paper',
    file_name: 'paper.pdf',
    file_size: 1024000,
    file_type: 'application/pdf',
    user_id: userId,
    thread_id: threadId,
    status: 'processing'
  })
  .select()
  .single()

if (error) throw error

// 2. Upload file to storage
const { data: fileData, error: uploadError } = await supabase.storage
  .from('documents')
  .upload(`${userId}/${threadId}/${document.id}`, file)

if (uploadError) throw uploadError

// 3. Process document content
const content = await extractTextFromFile(file)
await supabase.functions.invoke('vectorize', {
  body: {
    documentId: document.id,
    userId: userId,
    content: content,
    fileName: 'paper.pdf',
    fileType: 'application/pdf'
  }
})
```

#### Get Thread Documents

```javascript
const { data: documents, error } = await supabase
  .from('documents')
  .select(`
    id,
    title,
    file_name,
    file_size,
    file_type,
    status,
    created_at,
    vector_chunks(count)
  `)
  .eq('thread_id', threadId)
  .eq('user_id', userId)
  .order('created_at', { ascending: false })

if (error) throw error
console.log('Thread documents:', documents)
```

#### Update Document Status

```javascript
const { data: document, error } = await supabase
  .from('documents')
  .update({
    status: 'completed',
    updated_at: new Date().toISOString()
  })
  .eq('id', documentId)
  .eq('user_id', userId)
  .select()
  .single()

if (error) throw error
```

### Conversation Management

#### Add Conversation

```javascript
const { data: conversation, error } = await supabase
  .from('conversations')
  .insert({
    thread_id: threadId,
    user_id: userId,
    role: 'user', // or 'assistant'
    content: 'What is the main topic?',
    metadata: {
      source: 'chat',
      timestamp: new Date().toISOString()
    }
  })
  .select()
  .single()

if (error) throw error
```

#### Get Thread Conversations

```javascript
const { data: conversations, error } = await supabase
  .from('conversations')
  .select('*')
  .eq('thread_id', threadId)
  .eq('user_id', userId)
  .order('created_at', { ascending: true })

if (error) throw error
console.log('Thread conversations:', conversations)
```

### Vector Search

#### Similarity Search

```javascript
// Search within user's documents
const { data: chunks, error } = await supabase
  .rpc('match_documents', {
    query_embedding: embedding,
    match_threshold: 0.7,
    match_count: 5,
    p_user_id: userId,
    p_thread_id: threadId // optional
  })

if (error) throw error
console.log('Similar chunks:', chunks)
```

#### Cross-Thread Search

```javascript
// Search across multiple threads
const { data: chunks, error } = await supabase
  .rpc('match_documents_cross_thread', {
    query_embedding: embedding,
    match_threshold: 0.8,
    match_count: 10,
    p_user_id: userId,
    p_thread_ids: [threadId1, threadId2, threadId3]
  })

if (error) throw error
console.log('Cross-thread results:', chunks)
```

#### Custom Vector Search

```javascript
// Direct vector similarity search
const { data: chunks, error } = await supabase
  .from('vector_chunks')
  .select(`
    id,
    content,
    metadata,
    embedding,
    1 - (embedding <=> $1) as similarity
  `)
  .eq('user_id', userId)
  .gte('similarity', 0.7)
  .order('similarity', { ascending: false })
  .limit(5)

if (error) throw error
console.log('Vector search results:', chunks)
```

---

## Authentication

### JWT Token Management

```javascript
// Get current session
const { data: { session }, error } = await supabase.auth.getSession()

// Refresh session
const { data, error } = await supabase.auth.refreshSession()

// Sign out
const { error } = await supabase.auth.signOut()
```

### Row Level Security (RLS)

All tables implement RLS policies:

```sql
-- Example: Users can only access their own data
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);
```

### Service Role Access

For Edge Functions, use service role key:

```javascript
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)
```

---

## Error Handling

### Common Error Types

```typescript
interface APIError {
  message: string
  code: string
  details?: any
}

// Handle errors consistently
try {
  const { data, error } = await supabase.from('documents').select()
  if (error) throw error
} catch (error) {
  console.error('API Error:', error.message)
  // Handle specific error types
  if (error.code === 'PGRST116') {
    console.error('RLS policy violation')
  } else if (error.code === 'PGRST301') {
    console.error('Authentication required')
  }
}
```

### Error Codes

- **PGRST116**: Row Level Security policy violation
- **PGRST301**: Authentication required
- **PGRST302**: JWT token expired
- **PGRST303**: Invalid JWT token
- **PGRST304**: Insufficient permissions

### Retry Logic

```javascript
async function retryOperation(operation, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation()
    } catch (error) {
      if (i === maxRetries - 1) throw error
      if (error.code === 'PGRST302') {
        await supabase.auth.refreshSession()
        continue
      }
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)))
    }
  }
}
```

---

## Rate Limits

### Edge Function Limits

- **Requests per second**: 100 (Pro plan)
- **Concurrent executions**: 50 (Pro plan)
- **Memory usage**: 512MB per function
- **Execution time**: 60 seconds

### Database Limits

- **Connection pool**: 20 connections (Pro plan)
- **Query timeout**: 60 seconds
- **Vector operations**: 1000 per minute

### OpenAI API Limits

- **Requests per minute**: 3500 (GPT-4)
- **Tokens per minute**: 90,000 (GPT-4)
- **Embedding requests**: 3500 per minute

---

## Examples

### Complete Document Processing Flow

```javascript
async function processDocument(file, threadId, userId) {
  try {
    // 1. Create document record
    const { data: document } = await supabase
      .from('documents')
      .insert({
        title: file.name,
        file_name: file.name,
        file_size: file.size,
        file_type: file.type,
        user_id: userId,
        thread_id: threadId,
        status: 'processing'
      })
      .select()
      .single()

    // 2. Upload to storage
    await supabase.storage
      .from('documents')
      .upload(`${userId}/${threadId}/${document.id}`, file)

    // 3. Extract text content
    const content = await extractTextFromFile(file)

    // 4. Vectorize document
    const { data: vectorizeResult } = await supabase.functions.invoke('vectorize', {
      body: {
        documentId: document.id,
        userId: userId,
        content: content,
        fileName: file.name,
        fileType: file.type
      }
    })

    // 5. Update status
    await supabase
      .from('documents')
      .update({ status: 'completed' })
      .eq('id', document.id)

    return { success: true, documentId: document.id }

  } catch (error) {
    console.error('Document processing failed:', error)
    return { success: false, error: error.message }
  }
}
```

### RAG Query with Cross-Thread Search

```javascript
async function intelligentQuery(query, threadId, userId) {
  try {
    const response = await supabase.functions.invoke('rag-query', {
      body: {
        threadId: threadId,
        userId: userId,
        query: query,
        includeChatHistory: true,
        crossThreadSearch: true,
        maxThreadsSearch: 3,
        temperature: 0.7,
        model: 'gpt-4',
        maxResults: 8
      }
    })

    if (response.data.success) {
      // Save conversation
      await supabase
        .from('conversations')
        .insert([
          {
            thread_id: threadId,
            user_id: userId,
            role: 'user',
            content: query
          },
          {
            thread_id: threadId,
            user_id: userId,
            role: 'assistant',
            content: response.data.response
          }
        ])

      return response.data
    } else {
      throw new Error(response.data.error)
    }

  } catch (error) {
    console.error('RAG query failed:', error)
    throw error
  }
}
```

### Thread Management with Archival

```javascript
async function manageThread(threadId, userId, action) {
  try {
    switch (action) {
      case 'archive':
        await supabase
          .from('threads')
          .update({ status: 'archived' })
          .eq('id', threadId)
          .eq('user_id', userId)
        break

      case 'delete':
        const response = await supabase.functions.invoke('delete-thread', {
          body: {
            threadId: threadId,
            userId: userId,
            confirmDeletion: true,
            archiveConversations: true
          }
        })
        
        if (!response.data.success) {
          throw new Error(response.data.error)
        }
        break

      case 'restore':
        await supabase
          .from('threads')
          .update({ status: 'active' })
          .eq('id', threadId)
          .eq('user_id', userId)
        break

      default:
        throw new Error('Invalid action')
    }

    return { success: true }

  } catch (error) {
    console.error('Thread management failed:', error)
    return { success: false, error: error.message }
  }
}
```

---

## Best Practices

### Performance

1. **Batch Operations**: Use batch inserts for multiple records
2. **Connection Pooling**: Reuse database connections
3. **Caching**: Cache frequently accessed data
4. **Indexing**: Ensure proper database indexes
5. **Pagination**: Use pagination for large datasets

### Security

1. **Input Validation**: Validate all user inputs
2. **RLS Policies**: Always use Row Level Security
3. **JWT Validation**: Verify JWT tokens
4. **Rate Limiting**: Implement rate limiting
5. **Error Handling**: Don't expose sensitive information

### Monitoring

1. **Logging**: Log all API operations
2. **Metrics**: Track performance metrics
3. **Alerts**: Set up error alerts
4. **Health Checks**: Implement health check endpoints
5. **Audit Trail**: Maintain audit logs

---

## Support

For API support and questions:

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

Include the following when reporting issues:
- API endpoint and request details
- Error messages and stack traces
- Environment information
- Steps to reproduce 