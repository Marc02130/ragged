# Supabase Deployment Guide

## Overview

This guide provides comprehensive deployment instructions for the RAG application using Supabase CLI, including Edge Functions, custom tables with Row Level Security (RLS), and detailed deletion flow implementation.

## Prerequisites

### Required Tools
```bash
# Install Supabase CLI
npm install -g supabase

# Install Node.js and npm (for frontend)
node --version  # Should be 18+
npm --version   # Should be 8+

# Install Git (for version control)
git --version
```

### Required Accounts
- **Supabase Account**: Create at [supabase.com](https://supabase.com)
- **OpenAI Account**: Get API key from [platform.openai.com](https://platform.openai.com)

## Initial Setup

### 1. Create Supabase Project

```bash
# Login to Supabase
supabase login

# Create new project (or use existing)
supabase projects create --name ragged-app --org-id your-org-id

# Link to existing project (if already created)
supabase link --project-ref your-project-ref
```

### 2. Initialize Local Development

```bash
# Initialize Supabase in your project
supabase init

# Start local development
supabase start
```

### 3. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**
```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Application Configuration
NODE_ENV=development
```

## Database Schema Deployment

### 1. Apply Migrations

The application includes comprehensive migrations that set up the complete database schema:

```bash
# Apply all migrations in order
supabase db push

# Verify migrations
supabase db diff
```

**Migration Order:**
1. `00000_initial_schema.sql` - Base schema with tables and RLS
2. `00001_thread_deletion_function.sql` - Thread deletion cascade function
3. `00002_vector_chunks_optimization.sql` - Vector optimization indexes
4. `00003_fix_schema_consistency.sql` - Schema consistency fixes
5. `00004_add_user_preferences.sql` - User preferences system

### 2. Verify Database Setup

```bash
# Check database status
supabase db status

# View tables
supabase db inspect --schema public

# Test RLS policies
supabase db test --file test_rls.sql
```

### 3. Enable Required Extensions

```sql
-- Enable vector extension for embeddings
CREATE EXTENSION IF NOT EXISTS "vector";

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable crypto extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

## Edge Functions Deployment

### 1. Deploy All Edge Functions

```bash
# Deploy vectorization function
supabase functions deploy vectorize

# Deploy RAG query function
supabase functions deploy rag-query

# Deploy thread deletion function
supabase functions deploy delete-thread

# Verify deployment
supabase functions list
```

### 2. Set Edge Function Secrets

```bash
# Set OpenAI API key
supabase secrets set OPENAI_API_KEY=sk-your-openai-api-key

# Set Supabase service role key
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Verify secrets
supabase secrets list
```

### 3. Test Edge Functions

```bash
# Test vectorize function
curl -X POST https://your-project-ref.supabase.co/functions/v1/vectorize \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "document",
    "documentId": "test-doc-id",
    "userId": "test-user-id"
  }'

# Test RAG query function
curl -X POST https://your-project-ref.supabase.co/functions/v1/rag-query \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "threadId": "test-thread-id",
    "userId": "test-user-id",
    "query": "What is this document about?"
  }'

# Test delete-thread function
curl -X POST https://your-project-ref.supabase.co/functions/v1/delete-thread \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "threadId": "test-thread-id",
    "userId": "test-user-id",
    "confirmDeletion": true
  }'
```

## Storage Bucket Configuration

### 1. Create Storage Buckets

```bash
# Create documents bucket
supabase storage create documents

# Create archives bucket
supabase storage create archives

# Create temp bucket
supabase storage create temp

# List buckets
supabase storage list
```

### 2. Configure Storage Policies

```sql
-- Documents bucket policy (user-scoped access)
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

-- Archives bucket policy
CREATE POLICY "Users can access own archives" ON storage.objects
  FOR ALL USING (
    bucket_id = 'archives' AND 
    auth.uid()::text = (storage.foldername(name))[1]
  );

-- Temp bucket policy (temporary files)
CREATE POLICY "Users can manage temp files" ON storage.objects
  FOR ALL USING (
    bucket_id = 'temp' AND 
    auth.uid()::text = (storage.foldername(name))[1]
  );
```

## Row Level Security (RLS) Configuration

### 1. Verify RLS Policies

All tables have RLS enabled with user-scoped policies:

```sql
-- Verify RLS is enabled on all tables
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('user_profiles', 'threads', 'documents', 'conversations', 'vector_chunks');

-- Check RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';
```

### 2. Test RLS Policies

```sql
-- Test user isolation
-- As user A
SET LOCAL ROLE authenticated;
SET LOCAL "request.jwt.claim.sub" TO 'user-a-id';

-- Should only see user A's data
SELECT * FROM threads WHERE user_id = 'user-a-id';

-- As user B
SET LOCAL "request.jwt.claim.sub" TO 'user-b-id';

-- Should only see user B's data
SELECT * FROM threads WHERE user_id = 'user-b-id';
```

## Thread Deletion Flow Implementation

### 1. Deletion Process Overview

The thread deletion process follows the PRD specification:

1. **User Confirmation**: Frontend shows confirmation dialog
2. **OpenAI Thread Deletion**: Delete the OpenAI thread
3. **Conversation Retrieval**: Get full conversation history
4. **Vectorization**: Process conversation into embeddings
5. **Storage**: Save as TXT file in Supabase Storage
6. **Vector Storage**: Store embeddings in PGVector
7. **Database Archive**: Mark as archived in conversations table

### 2. Deletion Function Implementation

```typescript
// delete-thread/index.ts - Key Implementation

async function archiveThread(threadId: string, userId: string): Promise<{ success: boolean; archivedConversations?: number; error?: string }> {
  try {
    // 1. Get thread information
    const { data: thread, error: threadError } = await supabase
      .from('threads')
      .select('*')
      .eq('id', threadId)
      .eq('user_id', userId)
      .single()

    if (threadError || !thread) {
      return { success: false, error: 'Thread not found or access denied' }
    }

    // 2. Get all conversations for the thread
    const { data: conversations, error: convError } = await supabase
      .from('conversations')
      .select('*')
      .eq('thread_id', threadId)
      .eq('user_id', userId)
      .order('created_at', { ascending: true })

    if (convError) {
      return { success: false, error: `Failed to retrieve thread conversations: ${convError.message}` }
    }

    // 3. Create comprehensive thread archive
    const archiveContent = createThreadArchive(thread, conversations || [])
    
    // 4. Generate embedding for the archive
    const [archiveEmbedding] = await embeddings.embedDocuments([archiveContent])

    // 5. Store archive in vector_chunks table
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
          conversation_count: conversations?.length || 0,
          archive_date: new Date().toISOString(),
          date_range: {
            start: thread.created_at,
            end: thread.updated_at
          },
          original_thread_status: thread.status
        },
        chunk_index: 0
      })

    if (insertError) {
      return { success: false, error: `Failed to store thread archive: ${insertError.message}` }
    }

    // 6. Save archive as TXT file in Storage
    const archiveFileName = `archives/users/${userId}/threads/${threadId}/archive_${Date.now()}.txt`
    const { error: storageError } = await supabase.storage
      .from('archives')
      .upload(archiveFileName, archiveContent, {
        contentType: 'text/plain',
        metadata: {
          thread_id: threadId,
          thread_title: thread.title,
          conversation_count: conversations?.length || 0,
          archive_date: new Date().toISOString()
        }
      })

    if (storageError) {
      console.warn(`Failed to save archive to storage: ${storageError.message}`)
      // Continue with database archive even if storage fails
    }

    return { success: true, archivedConversations: conversations?.length || 0 }

  } catch (error) {
    console.error('Thread archival error:', error)
    return { success: false, error: `Thread archival failed: ${error.message}` }
  }
}
```

### 3. Archive Content Generation

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
  ]

  conversations.forEach((conv, index) => {
    archive.push(
      `[${index + 1}] ${conv.role.toUpperCase()} (${new Date(conv.created_at).toLocaleString()}):`,
      conv.content,
      ''
    )
  })

  return archive.join('\n')
}
```

### 4. Cascade Deletion Function

```sql
-- Database function for cascading deletion
CREATE OR REPLACE FUNCTION delete_thread_cascade(
  p_thread_id UUID,
  p_user_id UUID
) RETURNS VOID AS $$
BEGIN
  -- Verify thread belongs to user
  IF NOT EXISTS (
    SELECT 1 FROM threads 
    WHERE id = p_thread_id AND user_id = p_user_id
  ) THEN
    RAISE EXCEPTION 'Thread not found or access denied';
  END IF;

  -- Delete vector chunks associated with the thread
  DELETE FROM vector_chunks 
  WHERE user_id = p_user_id 
    AND thread_id = p_thread_id;

  -- Delete conversations in the thread
  DELETE FROM conversations 
  WHERE thread_id = p_thread_id AND user_id = p_user_id;

  -- Delete documents associated with the thread
  DELETE FROM documents 
  WHERE thread_id = p_thread_id AND user_id = p_user_id;

  -- Finally, delete the thread itself
  DELETE FROM threads 
  WHERE id = p_thread_id AND user_id = p_user_id;

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Multiple Thread Handling

### 1. Thread Management Functions

```sql
-- Function to get user's threads with document counts
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

### 2. Cross-Thread Search Implementation

```typescript
// rag-query/index.ts - Cross-thread search

async function performSimilaritySearch(request: RAGQueryRequest, queryEmbedding: number[]) {
  const crossThreadSearch = request.crossThreadSearch !== false // Default to true
  
  if (crossThreadSearch) {
    // Get user's threads for cross-thread search
    const { data: userThreads, error: threadsError } = await supabase
      .from('threads')
      .select('id, title, created_at')
      .eq('user_id', request.userId)
      .order('updated_at', { ascending: false })
      .limit(5) // Limit to 5 most recent threads

    // Search across multiple threads
    for (const thread of userThreads) {
      // Perform similarity search for each thread
      const threadResults = await searchThread(thread.id, queryEmbedding, request)
      // Combine and rank results
    }
  } else {
    // Search only current thread
    return await searchThread(request.threadId, queryEmbedding, request)
  }
}
```

## Production Deployment

### 1. Production Environment Setup

```bash
# Set production environment variables
supabase secrets set --env prod OPENAI_API_KEY=sk-your-prod-openai-key
supabase secrets set --env prod SUPABASE_SERVICE_ROLE_KEY=your-prod-service-role-key

# Deploy to production
supabase db push --env prod
supabase functions deploy vectorize --env prod
supabase functions deploy rag-query --env prod
supabase functions deploy delete-thread --env prod
```

### 2. Monitoring and Logging

```bash
# View Edge Function logs
supabase functions logs vectorize --env prod
supabase functions logs rag-query --env prod
supabase functions logs delete-thread --env prod

# View database logs
supabase db logs --env prod
```

### 3. Performance Optimization

```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vector_chunks_user_thread 
ON vector_chunks(user_id, thread_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_thread_time 
ON conversations(user_id, thread_id, created_at);

-- Analyze table statistics
ANALYZE vector_chunks;
ANALYZE conversations;
ANALYZE threads;
ANALYZE documents;
```

## Testing and Verification

### 1. Integration Tests

```bash
# Test complete workflow
npm run test:integration

# Test Edge Functions
npm run test:edge-functions

# Test database functions
npm run test:database
```

### 2. Load Testing

```bash
# Test with multiple concurrent users
npm run test:load

# Test vectorization performance
npm run test:vectorization

# Test RAG query performance
npm run test:rag-query
```

### 3. Security Testing

```bash
# Test RLS policies
npm run test:security

# Test authentication
npm run test:auth

# Test user isolation
npm run test:isolation
```

## Troubleshooting

### Common Issues

1. **Edge Function Deployment Failures**
   ```bash
   # Check function logs
   supabase functions logs vectorize
   
   # Verify secrets
   supabase secrets list
   
   # Test function locally
   supabase functions serve vectorize
   ```

2. **Database Migration Issues**
   ```bash
   # Reset database
   supabase db reset
   
   # Check migration status
   supabase db diff
   
   # Apply migrations manually
   supabase db push
   ```

3. **RLS Policy Issues**
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

### Performance Issues

1. **Slow Vector Searches**
   ```sql
   -- Check vector index
   SELECT * FROM pg_indexes WHERE indexname LIKE '%vector%';
   
   -- Rebuild index
   REINDEX INDEX CONCURRENTLY idx_vector_chunks_embedding;
   ```

2. **High Memory Usage**
   ```sql
   -- Check connection count
   SELECT count(*) FROM pg_stat_activity;
   
   -- Check table sizes
   SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
   FROM pg_tables 
   WHERE schemaname = 'public';
   ```

## Maintenance

### Regular Maintenance Tasks

```bash
# Weekly: Check logs and performance
supabase functions logs --env prod
supabase db logs --env prod

# Monthly: Update dependencies
npm update
supabase update

# Quarterly: Review and optimize
ANALYZE vector_chunks;
ANALYZE conversations;
REINDEX INDEX CONCURRENTLY idx_vector_chunks_embedding;
```

This deployment guide ensures a complete, secure, and scalable implementation of the RAG application with proper thread deletion flow and multiple thread handling as specified in the PRD. 