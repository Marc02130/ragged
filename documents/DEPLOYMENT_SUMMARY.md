# Complete Deployment Summary: RAG Application

## Overview

This document provides a comprehensive summary of the RAG application deployment, including Supabase CLI instructions, Edge Functions, custom tables with RLS, detailed deletion flow, and multiple thread handling as specified in the PRD.

## 🚀 Quick Start Deployment

### Automated Deployment
```bash
# Make script executable
chmod +x scripts/deploy-supabase.sh

# Run automated deployment
./scripts/deploy-supabase.sh

# For production deployment
./scripts/deploy-supabase.sh --env production
```

### Manual Deployment Steps
```bash
# 1. Initialize Supabase project
supabase init
supabase link --project-ref YOUR_PROJECT_REF

# 2. Deploy database schema
supabase db push

# 3. Deploy Edge Functions
supabase functions deploy vectorize
supabase functions deploy rag-query
supabase functions deploy delete-thread

# 4. Configure secrets
supabase secrets set OPENAI_API_KEY=your-openai-key
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 📊 Database Schema Overview

### Core Tables (with RLS)

#### 1. **user_profiles**
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',  -- User preferences for RAG settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. **threads**
```sql
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    document_count INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. **documents**
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT,
    file_size INTEGER,
    file_type TEXT,
    content TEXT,
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    vector_status TEXT DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4. **conversations**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    vectorized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 5. **vector_chunks**
```sql
CREATE TABLE vector_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI embedding dimension
    metadata JSONB DEFAULT '{}',
    chunk_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Row Level Security (RLS) Policies

All tables have RLS enabled with user-scoped policies:

```sql
-- Example RLS policy for threads
CREATE POLICY "Users can view own threads" ON threads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own threads" ON threads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own threads" ON threads
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own threads" ON threads
    FOR DELETE USING (auth.uid() = user_id);
```

## 🔧 Edge Functions Architecture

### 1. **vectorize** Function
**Purpose**: Process documents and chat history into vector embeddings

**Key Features**:
- JWT authentication with user preferences loading
- Document chunking with Langchain.js
- OpenAI embeddings generation
- Batch processing with rate limiting
- User-scoped processing settings

**API Endpoint**: `POST /functions/v1/vectorize`

**Request Format**:
```json
{
  "type": "document" | "chat_history",
  "documentId": "uuid",
  "threadId": "uuid",
  "userId": "uuid",
  "content": "text content",
  "metadata": {},
  "options": {
    "maxChunks": 1000,
    "batchSize": 100,
    "chunkSize": 1000,
    "chunkOverlap": 200
  }
}
```

### 2. **rag-query** Function
**Purpose**: Perform RAG queries with context retrieval and response generation

**Key Features**:
- JWT authentication with user preferences
- Similarity search across documents and chat history
- Cross-thread search capability
- OpenAI GPT-4 response generation
- Conversation history saving

**API Endpoint**: `POST /functions/v1/rag-query`

**Request Format**:
```json
{
  "threadId": "uuid",
  "userId": "uuid",
  "query": "user question",
  "maxResults": 10,
  "includeChatHistory": true,
  "temperature": 0.7,
  "model": "gpt-4",
  "crossThreadSearch": true,
  "currentThreadPriority": true
}
```

### 3. **delete-thread** Function
**Purpose**: Handle thread deletion with comprehensive archival

**Key Features**:
- JWT authentication with user preferences
- Thread ownership verification
- Conversation history retrieval
- Vectorization of archived content
- Storage in Supabase Storage and PGVector
- Cascade deletion of associated data

**API Endpoint**: `POST /functions/v1/delete-thread`

**Request Format**:
```json
{
  "threadId": "uuid",
  "userId": "uuid",
  "confirmDeletion": true
}
```

## 🗑️ Thread Deletion Flow (PRD Specification)

### Deletion Process Overview

The thread deletion process follows the exact PRD specification:

```
1. User Confirmation → 2. OpenAI Thread Deletion → 3. Conversation Retrieval → 
4. Vectorization → 5. Storage → 6. Vector Storage → 7. Database Archive
```

### Detailed Implementation

#### Step 1: User Confirmation
```typescript
// Frontend confirmation dialog
const confirmDeletion = await showConfirmationDialog({
  title: "Delete Thread",
  message: `Are you sure you want to delete "${thread.title}"? This action cannot be undone.`,
  confirmText: "Delete Thread",
  cancelText: "Cancel"
});

if (!confirmDeletion) {
  return { success: false, error: "Deletion cancelled by user" };
}
```

#### Step 2: OpenAI Thread Deletion
```typescript
// Delete OpenAI thread (if applicable)
if (thread.openai_thread_id) {
  try {
    await openai.beta.threads.del(thread.openai_thread_id);
    console.log(`Deleted OpenAI thread: ${thread.openai_thread_id}`);
  } catch (error) {
    console.warn(`Failed to delete OpenAI thread: ${error.message}`);
    // Continue with archival even if OpenAI deletion fails
  }
}
```

#### Step 3: Conversation Retrieval
```typescript
// Get all conversations for the thread
const { data: conversations, error: convError } = await supabase
  .from('conversations')
  .select('*')
  .eq('thread_id', threadId)
  .eq('user_id', userId)
  .order('created_at', { ascending: true });

if (convError) {
  return { success: false, error: `Failed to retrieve conversations: ${convError.message}` };
}
```

#### Step 4: Vectorization
```typescript
// Create comprehensive thread archive
const archiveContent = createThreadArchive(thread, conversations);

// Generate embedding for the archive
const [archiveEmbedding] = await embeddings.embedDocuments([archiveContent]);
```

#### Step 5: Storage (Supabase Storage)
```typescript
// Save archive as TXT file in Storage
const archiveFileName = `archives/users/${userId}/threads/${threadId}/archive_${Date.now()}.txt`;
const { error: storageError } = await supabase.storage
  .from('archives')
  .upload(archiveFileName, archiveContent, {
    contentType: 'text/plain',
    metadata: {
      thread_id: threadId,
      thread_title: thread.title,
      conversation_count: conversations.length,
      archive_date: new Date().toISOString()
    }
  });
```

#### Step 6: Vector Storage (PGVector)
```typescript
// Store archive in vector_chunks table
const { error: insertError } = await supabase
  .from('vector_chunks')
  .insert({
    document_id: null,
    user_id: userId,
    content: archiveContent,
    embedding: archiveEmbedding,
    metadata: {
      is_thread_archive: true,
      thread_id: threadId,
      thread_title: thread.title,
      conversation_count: conversations.length,
      archive_date: new Date().toISOString(),
      date_range: {
        start: thread.created_at,
        end: thread.updated_at
      }
    },
    chunk_index: 0
  });
```

#### Step 7: Database Archive
```typescript
// Mark thread as archived in database
const { error: archiveError } = await supabase
  .from('threads')
  .update({ 
    status: 'archived',
    updated_at: new Date().toISOString()
  })
  .eq('id', threadId)
  .eq('user_id', userId);
```

### Archive Content Format

```typescript
function createThreadArchive(thread: any, conversations: any[]): string {
  const archive = [
    `THREAD ARCHIVE: ${thread.title}`,
    `Created: ${new Date(thread.created_at).toLocaleString()}`,
    `Last Activity: ${new Date(thread.updated_at).toLocaleString()}`,
    `Total Conversations: ${conversations.length}`,
    `Thread Status: ${thread.status}`,
    '',
    'CONVERSATION HISTORY:',
    '===================='
  ];

  conversations.forEach((conv, index) => {
    archive.push(
      `[${index + 1}] ${conv.role.toUpperCase()} (${new Date(conv.created_at).toLocaleString()}):`,
      conv.content,
      ''
    );
  });

  return archive.join('\n');
}
```

## 🔄 Multiple Thread Handling

### Thread Management Features

#### 1. **Thread Creation and Management**
```typescript
// Create new thread
const { data: thread, error } = await supabase
  .from('threads')
  .insert({
    user_id: userId,
    title: threadTitle,
    status: 'active'
  })
  .select()
  .single();
```

#### 2. **Thread Listing with Metadata**
```sql
-- Function to get user's threads with document and conversation counts
CREATE OR REPLACE FUNCTION get_user_threads(p_user_id UUID)
RETURNS TABLE (
  thread_id UUID,
  title TEXT,
  status TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  last_activity_at TIMESTAMP WITH TIME ZONE,
  document_count BIGINT,
  conversation_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    t.id,
    t.title,
    t.status,
    t.created_at,
    t.last_activity_at,
    COALESCE(doc_counts.count, 0) as document_count,
    COALESCE(conv_counts.count, 0) as conversation_count
  FROM threads t
  LEFT JOIN (
    SELECT thread_id, COUNT(*) as count 
    FROM documents 
    WHERE user_id = p_user_id 
    GROUP BY thread_id
  ) doc_counts ON t.id = doc_counts.thread_id
  LEFT JOIN (
    SELECT thread_id, COUNT(*) as count 
    FROM conversations 
    WHERE user_id = p_user_id 
    GROUP BY thread_id
  ) conv_counts ON t.id = conv_counts.thread_id
  WHERE t.user_id = p_user_id
  ORDER BY t.last_activity_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### 3. **Cross-Thread Search**
```typescript
// RAG query with cross-thread search capability
async function performSimilaritySearch(request: RAGQueryRequest, queryEmbedding: number[]) {
  const crossThreadSearch = request.crossThreadSearch !== false; // Default to true
  
  if (crossThreadSearch) {
    // Get user's recent threads for cross-thread search
    const { data: userThreads, error: threadsError } = await supabase
      .from('threads')
      .select('id, title, created_at')
      .eq('user_id', request.userId)
      .eq('status', 'active')
      .order('updated_at', { ascending: false })
      .limit(5); // Limit to 5 most recent threads

    let allResults = [];
    
    // Search across multiple threads
    for (const thread of userThreads) {
      const threadResults = await searchThread(thread.id, queryEmbedding, request);
      allResults.push(...threadResults.map(result => ({
        ...result,
        source_thread: thread.title,
        source_thread_id: thread.id
      })));
    }
    
    // Combine and rank results
    return rankAndFilterResults(allResults, request.maxResults);
  } else {
    // Search only current thread
    return await searchThread(request.threadId, queryEmbedding, request);
  }
}
```

#### 4. **Thread Archiving and Restoration**
```typescript
// Archive thread (soft delete)
const { error: archiveError } = await supabase
  .from('threads')
  .update({ 
    status: 'archived',
    updated_at: new Date().toISOString()
  })
  .eq('id', threadId)
  .eq('user_id', userId);

// Restore archived thread
const { error: restoreError } = await supabase
  .from('threads')
  .update({ 
    status: 'active',
    updated_at: new Date().toISOString()
  })
  .eq('id', threadId)
  .eq('user_id', userId);
```

## 🗄️ Storage Configuration

### Storage Buckets

#### 1. **documents** Bucket
- **Purpose**: Store uploaded documents
- **Path Structure**: `/users/{user_id}/threads/{thread_id}/{filename}`
- **Access**: User-scoped with RLS policies

#### 2. **archives** Bucket
- **Purpose**: Store thread archives after deletion
- **Path Structure**: `/users/{user_id}/threads/{thread_id}/archive_{timestamp}.txt`
- **Access**: User-scoped with RLS policies

#### 3. **temp** Bucket
- **Purpose**: Temporary file storage during processing
- **Path Structure**: `/users/{user_id}/temp/{filename}`
- **Access**: User-scoped with automatic cleanup

### Storage Policies

```sql
-- Documents bucket policies
CREATE POLICY "Users can upload own documents" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'documents' AND 
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can view own documents" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'documents' AND 
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can delete own documents" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'documents' AND 
    auth.uid()::text = (storage.foldername(name))[1]
  );
```

## 🔐 Security Implementation

### Authentication and Authorization

#### 1. **JWT Token Validation**
```typescript
// Enhanced authentication with user preferences
async function validateAuthAndGetPreferences(authHeader: string) {
  if (!authHeader) {
    return { user: null, preferences: {}, error: 'Authorization header required' };
  }

  const { data: { user }, error: authError } = await supabase.auth.getUser(
    authHeader.replace('Bearer ', '')
  );
  
  if (authError || !user) {
    return { user: null, preferences: {}, error: 'Invalid authentication token' };
  }

  // Get user preferences
  const { data: preferences, error: prefsError } = await supabase
    .rpc('get_user_preferences', { p_user_id: user.id });

  return { user, preferences: preferences || getDefaultPreferences() };
}
```

#### 2. **Resource Ownership Verification**
```typescript
// Verify user owns the resource
if (requestData.userId !== user.id) {
  return new Response(
    JSON.stringify({ error: 'Unauthorized access to resource' }),
    { status: 403, headers: { 'Content-Type': 'application/json' } }
  );
}
```

#### 3. **RLS Policy Enforcement**
```sql
-- All tables enforce user isolation
CREATE POLICY "Users can only access own data" ON threads
  FOR ALL USING (auth.uid() = user_id);
```

## 📈 Performance Optimization

### Database Indexes

```sql
-- Vector search optimization
CREATE INDEX idx_vector_chunks_embedding ON vector_chunks 
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- User and thread scoped queries
CREATE INDEX idx_vector_chunks_user_thread ON vector_chunks(user_id, thread_id);
CREATE INDEX idx_conversations_user_thread_time ON conversations(user_id, thread_id, created_at);
CREATE INDEX idx_documents_user_thread ON documents(user_id, thread_id);

-- Preferences optimization
CREATE INDEX idx_user_profiles_preferences ON user_profiles USING GIN (preferences);
```

### Edge Function Optimization

#### 1. **Batch Processing**
```typescript
// Process embeddings in batches
const batchSize = 100;
for (let i = 0; i < chunks.length; i += batchSize) {
  const batch = chunks.slice(i, i + batchSize);
  const embeddings = await embeddings.embedDocuments(batch);
  // Store batch
}
```

#### 2. **Rate Limiting**
```typescript
// Implement rate limiting for OpenAI API
const rateLimiter = new RateLimiter({
  maxRequests: 10,
  perMinute: 1
});

await rateLimiter.waitForToken();
const embedding = await openai.embeddings.create({ input: text });
```

## 🧪 Testing and Verification

### Integration Tests

```bash
# Test complete workflow
npm run test:integration

# Test Edge Functions
npm run test:edge-functions

# Test database functions
npm run test:database
```

### Load Testing

```bash
# Test with multiple concurrent users
npm run test:load

# Test vectorization performance
npm run test:vectorization

# Test RAG query performance
npm run test:rag-query
```

### Security Testing

```bash
# Test RLS policies
npm run test:security

# Test authentication
npm run test:auth

# Test user isolation
npm run test:isolation
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Supabase CLI installed and configured
- [ ] Environment variables set in `.env`
- [ ] OpenAI API key obtained
- [ ] Supabase project created and linked

### Database Deployment
- [ ] Migrations applied successfully
- [ ] RLS policies verified
- [ ] Required extensions enabled
- [ ] Indexes created for performance

### Edge Functions Deployment
- [ ] All functions deployed successfully
- [ ] Secrets configured
- [ ] Functions tested with valid JWT tokens
- [ ] Error handling verified

### Storage Configuration
- [ ] Storage buckets created
- [ ] Storage policies configured
- [ ] User-scoped access verified
- [ ] Archive functionality tested

### Security Verification
- [ ] JWT authentication working
- [ ] RLS policies enforced
- [ ] User isolation verified
- [ ] Resource ownership validated

### Performance Testing
- [ ] Vector search performance acceptable
- [ ] Document processing within limits
- [ ] Concurrent user handling tested
- [ ] Memory usage optimized

## 🚨 Troubleshooting

### Common Issues

#### 1. **Edge Function Deployment Failures**
```bash
# Check function logs
supabase functions logs vectorize

# Verify secrets
supabase secrets list

# Test function locally
supabase functions serve vectorize
```

#### 2. **Database Migration Issues**
```bash
# Reset database
supabase db reset

# Check migration status
supabase db diff

# Apply migrations manually
supabase db push
```

#### 3. **RLS Policy Issues**
```sql
-- Check RLS status
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Test policies
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claim.sub" TO 'test-user-id';
SELECT * FROM threads;
```

#### 4. **Vector Search Performance**
```sql
-- Check vector index
SELECT * FROM pg_indexes WHERE indexname LIKE '%vector%';

-- Rebuild index
REINDEX INDEX CONCURRENTLY idx_vector_chunks_embedding;
```

## 📚 Additional Resources

### Documentation
- [Supabase CLI Documentation](https://supabase.com/docs/reference/cli)
- [Edge Functions Guide](https://supabase.com/docs/guides/functions)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Vector Extension](https://supabase.com/docs/guides/ai/vector-embeddings)

### Code Examples
- [Complete Edge Function Examples](supabase/functions/)
- [Database Migration Files](supabase/migrations/)
- [Frontend Integration](src/lib/supabase.ts)

### Monitoring and Maintenance
- [Supabase Dashboard](https://supabase.com/dashboard)
- [Edge Function Logs](https://supabase.com/dashboard/project/[ref]/functions)
- [Database Monitoring](https://supabase.com/dashboard/project/[ref]/database)

This deployment summary provides a complete guide for implementing the RAG application with proper thread deletion flow and multiple thread handling as specified in the PRD. 