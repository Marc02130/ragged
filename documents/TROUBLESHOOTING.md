# RAGged Troubleshooting Guide

Comprehensive troubleshooting guide for common issues encountered when using the RAGged application.

## Table of Contents

- [Vector Database Issues](#vector-database-issues)
- [Thread Deletion Problems](#thread-deletion-problems)
- [Document Processing Issues](#document-processing-issues)
- [Authentication Problems](#authentication-problems)
- [Performance Issues](#performance-issues)
- [Edge Function Errors](#edge-function-errors)
- [Database Connection Issues](#database-connection-issues)
- [Storage Problems](#storage-problems)
- [OpenAI API Issues](#openai-api-issues)

---

## Vector Database Issues

### Problem: `pgvector` Extension Not Enabled

**Symptoms**:
- Error: `extension "vector" is not available`
- Vector operations fail
- Database migration errors

**Solution**:
```sql
-- Enable pgvector in Supabase Dashboard
-- 1. Go to Database > Extensions
-- 2. Find "vector" extension
-- 3. Click "Enable"

-- Or via SQL (if you have admin access)
CREATE EXTENSION IF NOT EXISTS "vector";
```

**Verification**:
```sql
-- Check if extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Problem: Vector Dimension Mismatch

**Symptoms**:
- Error: `vector dimension mismatch`
- Embedding insertion fails
- Vector search errors

**Solution**:
```sql
-- Ensure embeddings are 1536-dimensional (OpenAI ada-002)
-- Check your embedding model configuration

-- Verify vector column definition
\d vector_chunks
-- Should show: embedding VECTOR(1536)

-- If dimension is wrong, recreate the table
DROP TABLE IF EXISTS vector_chunks;
CREATE TABLE vector_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding VECTOR(1536), -- Must be 1536 for OpenAI ada-002
  metadata JSONB DEFAULT '{}',
  chunk_index INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Problem: Vector Search Performance Issues

**Symptoms**:
- Slow similarity searches
- Timeout errors on vector queries
- High CPU usage during searches

**Solution**:
```sql
-- Create optimized vector index
CREATE INDEX CONCURRENTLY ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- For better performance with large datasets
CREATE INDEX CONCURRENTLY ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 200);

-- Add covering index for metadata
CREATE INDEX ON vector_chunks (user_id, document_id) 
INCLUDE (content, metadata);
```

**Performance Tuning**:
```sql
-- Analyze table statistics
ANALYZE vector_chunks;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'vector_chunks';
```

### Problem: Vector Search Returns No Results

**Symptoms**:
- Similarity search returns empty results
- High similarity threshold not met
- No relevant documents found

**Solution**:
```javascript
// Lower the similarity threshold
const { data: chunks } = await supabase
  .rpc('match_documents', {
    query_embedding: embedding,
    match_threshold: 0.5, // Lower from 0.7 to 0.5
    match_count: 10,
    p_user_id: userId
  })

// Check if vectors exist for the user
const { data: vectorCount } = await supabase
  .from('vector_chunks')
  .select('id', { count: 'exact' })
  .eq('user_id', userId)

console.log('User has', vectorCount, 'vector chunks')
```

---

## Thread Deletion Problems

### Problem: Confirmation Dialog Not Working

**Symptoms**:
- Delete button doesn't work
- No confirmation dialog appears
- Thread deletion fails silently

**Solution**:
```javascript
// Ensure confirmDeletion is explicitly set to true
const response = await supabase.functions.invoke('delete-thread', {
  body: {
    threadId: threadId,
    userId: userId,
    confirmDeletion: true  // Must be explicitly true, not just truthy
  }
})

// Check response
if (!response.data.success) {
  console.error('Deletion failed:', response.data.error)
}
```

**Debug Steps**:
```javascript
// Add logging to track the request
console.log('Delete request:', {
  threadId,
  userId,
  confirmDeletion: true
})

// Check if thread exists and belongs to user
const { data: thread } = await supabase
  .from('threads')
  .select('id, title, user_id')
  .eq('id', threadId)
  .eq('user_id', userId)
  .single()

if (!thread) {
  console.error('Thread not found or access denied')
}
```

### Problem: Archive Not Created

**Symptoms**:
- Thread deleted but no archive created
- Conversations lost permanently
- Archive vector not stored

**Solution**:
```javascript
// Check if conversations exist in thread
const { data: conversations } = await supabase
  .from('conversations')
  .select('id, content, role')
  .eq('thread_id', threadId)
  .eq('user_id', userId)

if (conversations.length === 0) {
  console.log('No conversations to archive')
} else {
  console.log('Found', conversations.length, 'conversations to archive')
}

// Manually trigger archive creation
const response = await supabase.functions.invoke('delete-thread', {
  body: {
    threadId: threadId,
    userId: userId,
    confirmDeletion: true,
    archiveConversations: true, // Explicitly enable archiving
    preserveVectors: true
  }
})
```

**Check Archive Storage**:
```sql
-- Check if archive vectors were created
SELECT * FROM vector_chunks 
WHERE metadata->>'source_type' = 'thread_archive' 
AND metadata->>'archived_from' = 'your-thread-id';
```

### Problem: Deletion Cascade Fails

**Symptoms**:
- Thread deleted but documents remain
- Orphaned vector chunks
- Database constraint violations

**Solution**:
```sql
-- Check for orphaned records
SELECT 'documents' as table_name, COUNT(*) as orphaned_count
FROM documents d
LEFT JOIN threads t ON d.thread_id = t.id
WHERE t.id IS NULL AND d.thread_id IS NOT NULL

UNION ALL

SELECT 'vector_chunks' as table_name, COUNT(*) as orphaned_count
FROM vector_chunks vc
LEFT JOIN documents d ON vc.document_id = d.id
WHERE d.id IS NULL AND vc.document_id IS NOT NULL

UNION ALL

SELECT 'conversations' as table_name, COUNT(*) as orphaned_count
FROM conversations c
LEFT JOIN threads t ON c.thread_id = t.id
WHERE t.id IS NULL AND c.thread_id IS NOT NULL;
```

**Manual Cleanup**:
```sql
-- Clean up orphaned records (be careful!)
DELETE FROM vector_chunks 
WHERE document_id IN (
  SELECT d.id FROM documents d
  LEFT JOIN threads t ON d.thread_id = t.id
  WHERE t.id IS NULL
);

DELETE FROM documents 
WHERE thread_id IN (
  SELECT id FROM threads WHERE id NOT IN (
    SELECT DISTINCT thread_id FROM threads WHERE thread_id IS NOT NULL
  )
);
```

---

## Document Processing Issues

### Problem: Documents Stuck in "Processing" Status

**Symptoms**:
- Documents remain in processing state indefinitely
- No error messages displayed
- Vectorization never completes

**Solution**:
```javascript
// Check document status and error messages
const { data: document } = await supabase
  .from('documents')
  .select('id, title, status, error_message, created_at')
  .eq('id', documentId)
  .single()

console.log('Document status:', document.status)
if (document.error_message) {
  console.error('Processing error:', document.error_message)
}

// Re-process document if needed
if (document.status === 'processing') {
  // Get document content
  const { data: fileData } = await supabase.storage
    .from('documents')
    .download(`${userId}/${threadId}/${documentId}`)
  
  const content = await extractTextFromFile(fileData)
  
  // Re-invoke vectorization
  await supabase.functions.invoke('vectorize', {
    body: {
      documentId: documentId,
      userId: userId,
      content: content,
      fileName: document.file_name,
      fileType: document.file_type
    }
  })
}
```

**Check Edge Function Logs**:
```bash
# View vectorize function logs
supabase functions logs vectorize --follow

# Check for specific errors
supabase functions logs vectorize | grep -i error
```

### Problem: Large Document Timeouts

**Symptoms**:
- Large files fail to process
- Edge function timeouts
- Memory errors during processing

**Solution**:
```javascript
// Implement chunked processing for large files
async function processLargeDocument(file, threadId, userId) {
  const maxFileSize = 5 * 1024 * 1024 // 5MB
  
  if (file.size > maxFileSize) {
    // Split large file into chunks
    const chunks = await splitFileIntoChunks(file, maxFileSize)
    
    for (const chunk of chunks) {
      await processDocumentChunk(chunk, threadId, userId)
    }
  } else {
    await processDocument(file, threadId, userId)
  }
}

// Increase Edge Function timeout in supabase/config.toml
[functions.vectorize]
timeout = 300 # 5 minutes instead of default 60 seconds
```

### Problem: File Type Not Supported

**Symptoms**:
- Upload fails for certain file types
- "Unsupported file type" errors
- Text extraction fails

**Solution**:
```javascript
// Check supported file types
const supportedTypes = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'application/rtf'
]

// Validate file type before upload
function validateFileType(file) {
  if (!supportedTypes.includes(file.type)) {
    throw new Error(`Unsupported file type: ${file.type}`)
  }
  
  // Check file extension as backup
  const allowedExtensions = ['.pdf', '.docx', '.txt', '.rtf']
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  
  if (!allowedExtensions.includes(fileExtension)) {
    throw new Error(`Unsupported file extension: ${fileExtension}`)
  }
}
```

---

## Authentication Problems

### Problem: RLS Policy Violations

**Symptoms**:
- "Row Level Security policy violation" errors
- Access denied to user's own data
- Inconsistent permission errors

**Solution**:
```sql
-- Check current user authentication
SELECT auth.uid() as current_user;

-- Verify RLS policies exist
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE tablename IN ('documents', 'threads', 'conversations', 'vector_chunks');

-- Check if RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('documents', 'threads', 'conversations', 'vector_chunks');
```

**Fix RLS Policies**:
```sql
-- Recreate RLS policies if missing
-- Documents table
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents" ON documents
    FOR DELETE USING (auth.uid() = user_id);
```

### Problem: JWT Token Expiration

**Symptoms**:
- "JWT token expired" errors
- Authentication failures after idle time
- Session timeout issues

**Solution**:
```javascript
// Implement automatic token refresh
async function refreshSession() {
  const { data, error } = await supabase.auth.refreshSession()
  
  if (error) {
    console.error('Session refresh failed:', error)
    // Redirect to login
    window.location.href = '/login'
    return false
  }
  
  return true
}

// Check session before operations
async function checkAndRefreshSession() {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    return await refreshSession()
  }
  
  // Check if token expires soon (within 5 minutes)
  const expiresAt = new Date(session.expires_at * 1000)
  const now = new Date()
  const fiveMinutes = 5 * 60 * 1000
  
  if (expiresAt.getTime() - now.getTime() < fiveMinutes) {
    return await refreshSession()
  }
  
  return true
}

// Use before critical operations
async function performAuthenticatedOperation() {
  if (!(await checkAndRefreshSession())) {
    throw new Error('Authentication required')
  }
  
  // Proceed with operation
  const { data, error } = await supabase.from('documents').select()
}
```

### Problem: Service Role Key Issues

**Symptoms**:
- Edge Functions fail with permission errors
- Database operations fail in serverless functions
- "Insufficient permissions" errors

**Solution**:
```javascript
// Ensure service role key is used in Edge Functions
const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')! // Use service role, not anon key
)

// Verify environment variables are set
console.log('SUPABASE_URL:', Deno.env.get('SUPABASE_URL'))
console.log('SUPABASE_SERVICE_ROLE_KEY:', Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')?.substring(0, 10) + '...')
```

**Check Environment Variables**:
```bash
# Verify environment variables in Supabase Dashboard
# 1. Go to Settings > API
# 2. Copy the service_role key
# 3. Set in Edge Function environment

# Or via CLI
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

---

## Performance Issues

### Problem: Slow Vector Searches

**Symptoms**:
- Vector similarity searches take too long
- Timeout errors on complex queries
- High database CPU usage

**Solution**:
```sql
-- Optimize vector index
CREATE INDEX CONCURRENTLY ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 200);

-- Add covering index for common queries
CREATE INDEX ON vector_chunks (user_id, document_id) 
INCLUDE (content, metadata);

-- Partition large tables if needed
CREATE TABLE vector_chunks_partitioned (
  LIKE vector_chunks INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Analyze table statistics
ANALYZE vector_chunks;
```

**Query Optimization**:
```javascript
// Limit search scope
const { data: chunks } = await supabase
  .rpc('match_documents', {
    query_embedding: embedding,
    match_threshold: 0.7,
    match_count: 5, // Limit results
    p_user_id: userId,
    p_thread_id: threadId // Scope to specific thread
  })

// Use caching for repeated queries
const cacheKey = `search:${userId}:${queryHash}`
let results = await cache.get(cacheKey)
if (!results) {
  results = await performVectorSearch(query, userId)
  await cache.set(cacheKey, results, 300) // Cache for 5 minutes
}
```

### Problem: Memory Usage in Edge Functions

**Symptoms**:
- Edge Functions run out of memory
- Large document processing fails
- Function crashes with memory errors

**Solution**:
```javascript
// Implement streaming for large documents
async function processLargeDocumentStream(file, threadId, userId) {
  const chunkSize = 1024 * 1024 // 1MB chunks
  const chunks = []
  
  for (let i = 0; i < file.size; i += chunkSize) {
    const chunk = file.slice(i, i + chunkSize)
    chunks.push(chunk)
  }
  
  // Process chunks sequentially to avoid memory issues
  for (const chunk of chunks) {
    await processDocumentChunk(chunk, threadId, userId)
  }
}

// Reduce batch sizes
const BATCH_SIZE = 10 // Process 10 documents at a time instead of 100
for (let i = 0; i < documents.length; i += BATCH_SIZE) {
  const batch = documents.slice(i, i + BATCH_SIZE)
  await Promise.all(batch.map(doc => processDocument(doc)))
}
```

**Memory Monitoring**:
```javascript
// Monitor memory usage in Edge Functions
const startMemory = performance.memory?.usedJSHeapSize || 0

// Your processing code here

const endMemory = performance.memory?.usedJSHeapSize || 0
console.log(`Memory used: ${(endMemory - startMemory) / 1024 / 1024} MB`)

if (endMemory > 400 * 1024 * 1024) { // 400MB limit
  console.warn('High memory usage detected')
}
```

---

## Edge Function Errors

### Problem: Function Deployment Fails

**Symptoms**:
- `supabase functions deploy` fails
- Import errors in Edge Functions
- Deno compatibility issues

**Solution**:
```bash
# Check Deno configuration
cat supabase/functions/vectorize/deno.json

# Should include proper imports
{
  "imports": {
    "@langchain/openai": "npm:@langchain/openai@^0.0.14",
    "@langchain/textsplitters": "npm:@langchain/textsplitters@^0.0.1"
  }
}

# Deploy with verbose logging
supabase functions deploy vectorize --debug

# Check function logs
supabase functions logs vectorize --follow
```

**Common Import Issues**:
```typescript
// Correct imports for Deno Edge Functions
import { OpenAI } from "@langchain/openai"
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters"
import { createClient } from '@supabase/supabase-js'

// NOT: import { OpenAI } from "langchain/llms/openai" (old format)
```

### Problem: Function Timeout

**Symptoms**:
- Edge Functions timeout after 60 seconds
- Large document processing fails
- Long-running operations interrupted

**Solution**:
```toml
# Update supabase/config.toml
[functions.vectorize]
timeout = 300 # 5 minutes

[functions.rag-query]
timeout = 120 # 2 minutes

[functions.delete-thread]
timeout = 180 # 3 minutes
```

**Implement Progress Tracking**:
```javascript
// For long-running operations, implement progress updates
async function processLargeDocumentWithProgress(documentId, userId) {
  // Update status to processing
  await supabase
    .from('documents')
    .update({ status: 'processing', progress: 0 })
    .eq('id', documentId)
  
  // Process in chunks with progress updates
  const totalChunks = 100
  for (let i = 0; i < totalChunks; i++) {
    await processChunk(i)
    
    // Update progress every 10 chunks
    if (i % 10 === 0) {
      await supabase
        .from('documents')
        .update({ progress: Math.round((i / totalChunks) * 100) })
        .eq('id', documentId)
    }
  }
  
  // Mark as completed
  await supabase
    .from('documents')
    .update({ status: 'completed', progress: 100 })
    .eq('id', documentId)
}
```

---

## Database Connection Issues

### Problem: Connection Pool Exhaustion

**Symptoms**:
- "Too many connections" errors
- Database connection timeouts
- Connection pool full errors

**Solution**:
```javascript
// Implement connection pooling
import { Pool } from 'pg'

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20, // Limit concurrent connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})

// Use connection pooling in Edge Functions
async function withConnection(callback) {
  const client = await pool.connect()
  try {
    return await callback(client)
  } finally {
    client.release()
  }
}
```

**Monitor Connections**:
```sql
-- Check active connections
SELECT 
  datname,
  usename,
  application_name,
  client_addr,
  state,
  query_start,
  query
FROM pg_stat_activity 
WHERE datname = current_database();

-- Check connection limits
SHOW max_connections;
SHOW shared_preload_libraries;
```

### Problem: Query Timeout

**Symptoms**:
- Database queries timeout
- Long-running operations fail
- Connection hangs

**Solution**:
```javascript
// Set query timeout
const { data, error } = await supabase
  .from('vector_chunks')
  .select('*')
  .eq('user_id', userId)
  .timeout(30000) // 30 second timeout

// Implement retry logic with exponential backoff
async function retryQuery(queryFn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await queryFn()
    } catch (error) {
      if (i === maxRetries - 1) throw error
      
      if (error.message.includes('timeout')) {
        const delay = Math.pow(2, i) * 1000 // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay))
        continue
      }
      
      throw error
    }
  }
}
```

---

## Storage Problems

### Problem: File Upload Fails

**Symptoms**:
- File upload errors
- Storage bucket not found
- Permission denied errors

**Solution**:
```javascript
// Check storage bucket exists
const { data: buckets } = await supabase.storage.listBuckets()
console.log('Available buckets:', buckets.map(b => b.name))

// Create bucket if missing
if (!buckets.find(b => b.name === 'documents')) {
  const { data, error } = await supabase.storage.createBucket('documents', {
    public: false,
    allowedMimeTypes: ['application/pdf', 'text/plain', 'application/rtf'],
    fileSizeLimit: 10485760 // 10MB
  })
  
  if (error) {
    console.error('Failed to create bucket:', error)
  }
}

// Check storage policies
const { data: policies } = await supabase.storage.getBucket('documents')
console.log('Bucket policies:', policies)
```

**Fix Storage Policies**:
```sql
-- Create storage policies for documents bucket
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

CREATE POLICY "Users can update own documents" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'documents' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete own documents" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'documents' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );
```

### Problem: File Not Found

**Symptoms**:
- "File not found" errors when accessing uploaded files
- Broken file links
- Missing files in storage

**Solution**:
```javascript
// Check if file exists before accessing
async function checkFileExists(filePath) {
  const { data, error } = await supabase.storage
    .from('documents')
    .list(filePath.split('/').slice(0, -1).join('/'))
  
  if (error) {
    console.error('Storage list error:', error)
    return false
  }
  
  const fileName = filePath.split('/').pop()
  return data.some(file => file.name === fileName)
}

// Safe file download with error handling
async function safeDownloadFile(filePath) {
  try {
    const { data, error } = await supabase.storage
      .from('documents')
      .download(filePath)
    
    if (error) {
      console.error('Download error:', error)
      return null
    }
    
    return data
  } catch (error) {
    console.error('File access error:', error)
    return null
  }
}
```

---

## OpenAI API Issues

### Problem: Rate Limit Exceeded

**Symptoms**:
- "Rate limit exceeded" errors
- OpenAI API failures
- Embedding generation fails

**Solution**:
```javascript
// Implement rate limiting and retry logic
async function callOpenAIWithRetry(apiCall, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall()
    } catch (error) {
      if (error.message.includes('rate limit')) {
        const delay = Math.pow(2, i) * 1000 // Exponential backoff
        console.log(`Rate limited, waiting ${delay}ms before retry`)
        await new Promise(resolve => setTimeout(resolve, delay))
        continue
      }
      throw error
    }
  }
}

// Use for embeddings
const embeddings = await callOpenAIWithRetry(() => 
  openai.embeddings.create({
    model: 'text-embedding-ada-002',
    input: text
  })
)
```

**Monitor API Usage**:
```javascript
// Track API usage
let apiCallCount = 0
const API_LIMIT = 3500 // Requests per minute

function checkRateLimit() {
  apiCallCount++
  if (apiCallCount > API_LIMIT) {
    throw new Error('Rate limit exceeded')
  }
}

// Reset counter every minute
setInterval(() => {
  apiCallCount = 0
}, 60000)
```

### Problem: Invalid API Key

**Symptoms**:
- "Invalid API key" errors
- Authentication failures with OpenAI
- API calls rejected

**Solution**:
```javascript
// Validate API key format
function validateOpenAIKey(apiKey) {
  if (!apiKey || typeof apiKey !== 'string') {
    throw new Error('OpenAI API key is required')
  }
  
  if (!apiKey.startsWith('sk-')) {
    throw new Error('Invalid OpenAI API key format')
  }
  
  if (apiKey.length < 20) {
    throw new Error('OpenAI API key too short')
  }
}

// Test API key
async function testOpenAIKey(apiKey) {
  try {
    const response = await fetch('https://api.openai.com/v1/models', {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error(`API test failed: ${response.status}`)
    }
    
    return true
  } catch (error) {
    console.error('OpenAI API key test failed:', error)
    return false
  }
}
```

---

## Debug Mode

Enable comprehensive debugging:

```bash
# Set debug environment variables
export SUPABASE_DEBUG=1
export OPENAI_DEBUG=1

# Deploy with debug logging
supabase functions deploy --debug

# Monitor logs in real-time
supabase functions logs --follow
```

### Debug Tools

```javascript
// Add debug logging to Edge Functions
const DEBUG = Deno.env.get('DEBUG') === 'true'

function debugLog(message, data = null) {
  if (DEBUG) {
    console.log(`[DEBUG] ${message}`, data ? JSON.stringify(data, null, 2) : '')
  }
}

// Use throughout your code
debugLog('Processing document', { documentId, userId, fileSize })
```

---

## Getting Help

If you're still experiencing issues:

1. **Check the logs**: Use `supabase functions logs` to see detailed error messages
2. **Enable debug mode**: Set debug environment variables for more verbose output
3. **Check documentation**: Review the [API documentation](API.md) for correct usage
4. **Search issues**: Check existing [GitHub issues](https://github.com/your-repo/issues)
5. **Create new issue**: Include error messages, steps to reproduce, and environment details

### Issue Template

When reporting issues, include:

```
**Environment:**
- Node.js version: 
- Supabase plan: 
- Operating system: 
- Browser (if applicable): 

**Error:**
- Error message: 
- Stack trace: 
- When it occurs: 

**Steps to reproduce:**
1. 
2. 
3. 

**Expected behavior:**
- 

**Actual behavior:**
- 

**Additional context:**
- Screenshots: 
- Logs: 
- Configuration: 
``` 