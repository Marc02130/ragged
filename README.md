# RAGged: Intelligent Document Q&A with AI

A modern Retrieval-Augmented Generation (RAG) application that provides seamless document upload, vectorization, intelligent chat queries, and comprehensive thread management with archival capabilities. Built for individual users, researchers, and students who need to chat with their personal documents.

## 🚀 Key Features

- **Multi-Thread Support**: Create and manage multiple conversation threads per user
- **Document Processing**: Upload and vectorize PDF, DOCX, TXT, and RTF files
- **Intelligent Chat**: Context-aware responses using RAG with source attribution
- **Thread Archival**: Complete conversation preservation with vectorized archives
- **Cross-Thread Search**: Search across multiple threads for relevant context
- **Real-time Interface**: Modern React UI with drag-and-drop file upload
- **Secure Authentication**: Supabase Auth with JWT-based security
- **Vector Search**: Efficient similarity search using pgvector

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Edge Functions](#edge-functions)
- [Troubleshooting](#troubleshooting)
- [Security & Scoping](#security--scoping)
- [Performance Optimization](#performance-optimization)

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Supabase account with PGVector extension
- OpenAI API key (GPT-4 + text-embedding-ada-002)

### 1. Clone and Setup
```bash
git clone [repository-url]
cd ragged
cp env.example .env
```

### 2. Configure Environment
```bash
# Edit .env with your credentials
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_key
```

### 3. Deploy Backend
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Deploy database and Edge Functions
./scripts/deploy.sh
```

### 4. Start Development
```bash
npm install
npm run dev
```

---

## 🔧 Detailed Setup

### Supabase Project Configuration

1. **Create Supabase Project**
   ```bash
   # Create new project at https://supabase.com
   # Enable PGVector extension in Database > Extensions
   ```

2. **Configure Authentication**
   - Go to Authentication > Settings
   - Enable Email confirmations (optional)
   - Configure redirect URLs for your domain

3. **Set up Storage**
   - Go to Storage > Create bucket: `documents`
   - Set bucket to private
   - Configure RLS policies (auto-configured by deployment script)

### Database Schema

The application uses the following custom tables:

#### `user_profiles`
- User profile information
- Auto-created on signup
- Scoped to individual users

#### `documents`
- Document metadata and content
- Supports multiple file types
- Processing status tracking

#### `vector_chunks`
- Document embeddings for RAG
- 1536-dimensional vectors (OpenAI ada-002)
- Metadata for chunk context

#### `threads`
- Conversation threads per user
- Multiple threads per user supported
- Status tracking (active/archived)

#### `conversations`
- Chat messages within threads
- User/assistant role support
- Metadata for message context

### Edge Functions Deployment

The deployment script sets up three core Edge Functions:

```bash
# Manual deployment (if needed)
supabase functions deploy vectorize
supabase functions deploy rag-query
supabase functions deploy delete-thread
```

---

## 📚 API Documentation

### Edge Functions

#### 1. Vectorize Function
**Endpoint**: `POST /functions/v1/vectorize`

Processes and vectorizes uploaded documents.

```typescript
interface VectorizeRequest {
  documentId: string
  userId: string
  content: string
  fileName: string
  fileType: string
}

interface VectorizeResponse {
  success: boolean
  vectorCount: number
  processedChunks: number
  totalChunks: number
  message?: string
  error?: string
}
```

**Usage**:
```javascript
const response = await supabase.functions.invoke('vectorize', {
  body: {
    documentId: 'doc-uuid',
    userId: 'user-uuid',
    content: 'document content...',
    fileName: 'document.pdf',
    fileType: 'application/pdf'
  }
})
```

#### 2. RAG Query Function
**Endpoint**: `POST /functions/v1/rag-query`

Performs intelligent document queries with RAG.

```typescript
interface RAGQueryRequest {
  threadId: string
  userId: string
  query: string
  maxResults?: number
  includeChatHistory?: boolean
  temperature?: number
  model?: string
  crossThreadSearch?: boolean
  maxThreadsSearch?: number
}

interface RAGQueryResponse {
  success: boolean
  response: string
  sources: Array<{
    content: string
    metadata: Record<string, any>
    similarity: number
    sourceType: 'document' | 'chat_history' | 'thread_archive'
  }>
  performance: {
    searchTime: number
    generationTime: number
    totalTime: number
    tokensUsed: number
  }
  fallbackGenerated?: boolean
  error?: string
}
```

**Usage**:
```javascript
const response = await supabase.functions.invoke('rag-query', {
  body: {
    threadId: 'thread-uuid',
    userId: 'user-uuid',
    query: 'What is the main topic?',
    includeChatHistory: true,
    crossThreadSearch: true
  }
})
```

#### 3. Delete Thread Function
**Endpoint**: `POST /functions/v1/delete-thread`

Archives and deletes threads with confirmation.

```typescript
interface DeleteThreadRequest {
  threadId: string
  userId: string
  confirmDeletion: boolean
}

interface DeleteThreadResponse {
  success: boolean
  message?: string
  error?: string
}
```

**Usage**:
```javascript
const response = await supabase.functions.invoke('delete-thread', {
  body: {
    threadId: 'thread-uuid',
    userId: 'user-uuid',
    confirmDeletion: true
  }
})
```

### Database API

#### Thread Management
```javascript
// Create thread
const { data: thread } = await supabase
  .from('threads')
  .insert({
    title: 'New Thread',
    user_id: userId
  })
  .select()
  .single()

// Get user threads
const { data: threads } = await supabase
  .from('threads')
  .select('*')
  .eq('user_id', userId)
  .order('updated_at', { ascending: false })
```

#### Document Management
```javascript
// Upload document
const { data: document } = await supabase
  .from('documents')
  .insert({
    title: 'Document Title',
    file_name: 'document.pdf',
    user_id: userId,
    thread_id: threadId
  })
  .select()
  .single()

// Get thread documents
const { data: documents } = await supabase
  .from('documents')
  .select('*')
  .eq('thread_id', threadId)
  .eq('user_id', userId)
```

#### Vector Search
```javascript
// Similarity search
const { data: chunks } = await supabase
  .rpc('match_documents', {
    query_embedding: embedding,
    match_threshold: 0.7,
    match_count: 5,
    p_user_id: userId
  })
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Vector Database Errors

**Problem**: `pgvector` extension not enabled
```sql
-- Enable pgvector in Supabase Dashboard
-- Database > Extensions > Enable "vector"
```

**Problem**: Vector dimension mismatch
```sql
-- Ensure embeddings are 1536-dimensional
-- Check OpenAI model: text-embedding-ada-002
```

**Problem**: Vector search performance
```sql
-- Create optimized index
CREATE INDEX ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

#### 2. Thread Deletion Warnings

**Problem**: Confirmation dialog not working
```javascript
// Ensure confirmDeletion is set to true
const response = await supabase.functions.invoke('delete-thread', {
  body: {
    threadId: threadId,
    userId: userId,
    confirmDeletion: true  // Must be explicitly true
  }
})
```

**Problem**: Archive not created
- Check if conversations exist in thread
- Verify `storeThreadArchive` function is called
- Check vector storage permissions

#### 3. Document Processing Issues

**Problem**: Documents stuck in "processing" status
```javascript
// Check document status
const { data: doc } = await supabase
  .from('documents')
  .select('status, error_message')
  .eq('id', documentId)
  .single()

// Re-process if needed
await supabase.functions.invoke('vectorize', {
  body: { documentId, userId, content, fileName, fileType }
})
```

**Problem**: Large document timeouts
- Increase Edge Function timeout in `supabase/config.toml`
- Implement chunked processing for files > 5MB

#### 4. Authentication Issues

**Problem**: RLS policy violations
```sql
-- Check user authentication
SELECT auth.uid() as current_user;

-- Verify RLS policies
SELECT * FROM pg_policies WHERE tablename = 'documents';
```

**Problem**: JWT token expiration
```javascript
// Refresh session
const { data, error } = await supabase.auth.refreshSession()
```

#### 5. Performance Issues

**Problem**: Slow vector searches
```sql
-- Optimize vector index
CREATE INDEX CONCURRENTLY ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 200);
```

**Problem**: Memory usage in Edge Functions
- Reduce batch sizes in vectorization
- Implement streaming for large documents
- Use connection pooling

### Debug Mode

Enable debug logging:
```bash
# Set environment variable
export SUPABASE_DEBUG=1

# Deploy with debug
supabase functions deploy --debug
```

### Monitoring

Monitor Edge Function performance:
```bash
# View function logs
supabase functions logs

# Monitor specific function
supabase functions logs rag-query --follow
```

---

## 🔒 Security & Scoping

### Row Level Security (RLS)

All tables implement RLS policies for user-scoped access:

```sql
-- Example: Documents table
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);
```

### User Scoping

- **Documents**: Scoped to `user_id`
- **Threads**: Scoped to `user_id`
- **Conversations**: Scoped to `user_id` and `thread_id`
- **Vector Chunks**: Scoped to `user_id` and `document_id`

### Multi-Thread Support

Users can create multiple threads:
```javascript
// Create multiple threads
const threads = [
  { title: 'Research Paper', user_id: userId },
  { title: 'Meeting Notes', user_id: userId },
  { title: 'Project Documentation', user_id: userId }
]

// Each thread is isolated
const { data: threadDocs } = await supabase
  .from('documents')
  .select('*')
  .eq('thread_id', specificThreadId)
  .eq('user_id', userId)
```

### Cross-Thread Search

Enable cross-thread search in RAG queries:
```javascript
const response = await supabase.functions.invoke('rag-query', {
  body: {
    threadId: currentThreadId,
    userId: userId,
    query: 'Search across all threads',
    crossThreadSearch: true,
    maxThreadsSearch: 5
  }
})
```

---

## ⚡ Performance Optimization

### Vector Search Optimization

```sql
-- Optimize vector index for similarity search
CREATE INDEX ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Add covering index for metadata
CREATE INDEX ON vector_chunks (user_id, document_id) 
INCLUDE (content, metadata);
```

### Batch Processing

```javascript
// Process documents in batches
const batchSize = 10
for (let i = 0; i < documents.length; i += batchSize) {
  const batch = documents.slice(i, i + batchSize)
  await Promise.all(batch.map(doc => processDocument(doc)))
}
```

### Caching Strategy

```javascript
// Cache frequently accessed data
const cacheKey = `user:${userId}:threads`
const cachedThreads = await redis.get(cacheKey)
if (!cachedThreads) {
  const threads = await fetchThreads(userId)
  await redis.setex(cacheKey, 3600, JSON.stringify(threads))
}
```

### Connection Pooling

```javascript
// Use connection pooling for database
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})
```

---

## 📊 Monitoring & Analytics

### Key Metrics

- **Document Processing Time**: Average time to vectorize documents
- **Query Response Time**: RAG query performance
- **Vector Search Accuracy**: Similarity score distributions
- **User Engagement**: Thread creation and conversation frequency

### Health Checks

```javascript
// Health check endpoint
app.get('/health', async (req, res) => {
  const checks = {
    database: await checkDatabase(),
    vectorSearch: await checkVectorSearch(),
    openai: await checkOpenAI(),
    storage: await checkStorage()
  }
  
  const healthy = Object.values(checks).every(check => check.status === 'ok')
  res.status(healthy ? 200 : 503).json(checks)
})
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Install dependencies
npm install

# Run tests
npm run test
npm run test:e2e

# Run linting
npm run lint

# Format code
npm run format
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📊 Diagrams

### Data Flow Diagrams
- **[Upload-to-Query Flow](docs/diagrams/upload-to-query-flow.md)** - Complete data flow from document upload through vectorization to RAG query execution
- **[Thread Deletion Flow](docs/diagrams/thread-deletion-flow.md)** - Archive and deletion process with vector preservation and confirmation workflow
- **[Multi-Thread Architecture](docs/diagrams/multi-thread-architecture.md)** - User isolation, thread management, and cross-thread search capabilities

### Database & System Diagrams
- **[Database Schema](docs/diagrams/database-schema.md)** - Complete database structure, relationships, RLS policies, and indexes
- **[Diagrams Overview](docs/diagrams/README.md)** - Guide to viewing and understanding all diagrams

### Viewing Diagrams
These diagrams use Mermaid syntax and render automatically in:
- GitHub/GitLab markdown files
- VS Code with "Mermaid Preview" extension
- Online at [mermaid.live](https://mermaid.live)

---

## 📚 Additional Documentation

- **[API Reference](docs/API.md)** - Complete Edge Function and database API documentation
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Security Guide](docs/SECURITY.md)** - Security and scoping documentation
- **[Best Practices Guide](docs/BEST_PRACTICES.md)** - Vector storage scaling, RLS setup, and performance optimization

---

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

For urgent issues, please include:
- Error messages and stack traces
- Steps to reproduce
- Environment details (Node.js version, Supabase plan, etc.)
- Screenshots if applicable
