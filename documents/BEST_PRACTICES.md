# Best Practices Guide

This guide covers best practices for scaling vector storage in Supabase PGVector, implementing robust Row Level Security (RLS), and managing user/thread privacy with archive retention and multiple thread support.

## 🚀 Vector Storage Scaling Best Practices

### 1. PGVector Index Optimization

#### Choose the Right Index Type
```sql
-- For lab-scale data (< 1M vectors): Use IVFFlat
CREATE INDEX idx_vector_chunks_embedding ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- For larger datasets (> 1M vectors): Use HNSW
CREATE INDEX idx_vector_chunks_embedding_hnsw ON vector_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

#### Index Configuration Guidelines
```sql
-- Optimal IVFFlat configuration for different scales
-- Small dataset (< 100K vectors)
CREATE INDEX idx_small_scale ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 50);

-- Medium dataset (100K - 1M vectors)
CREATE INDEX idx_medium_scale ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Large dataset (1M - 10M vectors)
CREATE INDEX idx_large_scale ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 200);

-- Very large dataset (> 10M vectors): Consider HNSW
CREATE INDEX idx_very_large_scale ON vector_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64, ef_search = 40);
```

#### Performance Monitoring
```sql
-- Monitor index performance
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%vector%';

-- Check index size
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes 
WHERE tablename = 'vector_chunks';
```

### 2. Vector Storage Optimization

#### Efficient Vector Storage
```sql
-- Use appropriate data types
CREATE TABLE vector_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- Fixed dimension for OpenAI ada-002
    metadata JSONB DEFAULT '{}',
    chunk_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add compression for metadata
ALTER TABLE vector_chunks ALTER COLUMN metadata SET COMPRESSION lz4;
```

#### Batch Processing for Vector Insertion
```javascript
// Efficient batch insertion
const batchInsertVectors = async (vectors, batchSize = 100) => {
  const batches = [];
  for (let i = 0; i < vectors.length; i += batchSize) {
    batches.push(vectors.slice(i, i + batchSize));
  }

  for (const batch of batches) {
    const { error } = await supabase
      .from('vector_chunks')
      .insert(batch);
    
    if (error) {
      console.error('Batch insertion error:', error);
      throw error;
    }
  }
};

// Usage example
const vectors = [
  { document_id: 'doc-1', user_id: 'user-1', content: 'chunk 1', embedding: [0.1, 0.2, ...] },
  { document_id: 'doc-1', user_id: 'user-1', content: 'chunk 2', embedding: [0.3, 0.4, ...] },
  // ... more vectors
];

await batchInsertVectors(vectors, 50); // Process in batches of 50
```

#### Vector Search Optimization
```sql
-- Optimized vector search function
CREATE OR REPLACE FUNCTION match_documents_optimized(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    p_user_id UUID DEFAULT NULL,
    p_thread_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        vc.id,
        vc.content,
        vc.metadata,
        1 - (vc.embedding <=> query_embedding) AS similarity
    FROM vector_chunks vc
    WHERE vc.user_id = COALESCE(p_user_id, vc.user_id)
        AND (p_thread_id IS NULL OR vc.metadata->>'thread_id' = p_thread_id::text)
        AND 1 - (vc.embedding <=> query_embedding) > match_threshold
    ORDER BY vc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

### 3. Memory and Performance Management

#### Connection Pooling
```javascript
// Optimize database connections
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY,
  {
    db: {
      pool: {
        min: 2,
        max: 10,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
      }
    }
  }
);
```

#### Query Optimization
```sql
-- Use prepared statements for repeated queries
PREPARE vector_search(UUID, VECTOR(1536), FLOAT, INT) AS
SELECT id, content, metadata, 1 - (embedding <=> $2) AS similarity
FROM vector_chunks
WHERE user_id = $1
  AND 1 - (embedding <=> $2) > $3
ORDER BY embedding <=> $2
LIMIT $4;

-- Execute prepared statement
EXECUTE vector_search('user-uuid', '[0.1,0.2,...]'::vector, 0.7, 10);
```

## 🔒 RLS Setup for User/Thread Privacy

### 1. Comprehensive RLS Policies

#### User Profiles RLS
```sql
-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Comprehensive user profile policies
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own profile" ON user_profiles
    FOR DELETE USING (auth.uid() = user_id);
```

#### Threads RLS with Archive Support
```sql
-- Enable RLS
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;

-- Thread policies with archive consideration
CREATE POLICY "Users can view own threads" ON threads
    FOR SELECT USING (
        auth.uid() = user_id AND 
        status IN ('active', 'archived')
    );

CREATE POLICY "Users can insert own threads" ON threads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own threads" ON threads
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own threads" ON threads
    FOR DELETE USING (auth.uid() = user_id);

-- Service role policy for archive operations
CREATE POLICY "Service role can manage threads" ON threads
    FOR ALL USING (auth.role() = 'service_role');
```

#### Documents RLS with Privacy Controls
```sql
-- Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Document policies with thread scoping
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads 
            WHERE user_id = auth.uid() AND status = 'active'
        )
    );

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents" ON documents
    FOR DELETE USING (auth.uid() = user_id);
```

#### Vector Chunks RLS with Archive Integration
```sql
-- Enable RLS
ALTER TABLE vector_chunks ENABLE ROW LEVEL SECURITY;

-- Vector chunk policies including archives
CREATE POLICY "Users can view own vector chunks" ON vector_chunks
    FOR SELECT USING (
        auth.uid() = user_id AND
        (
            -- Active document vectors
            (document_id IS NOT NULL AND 
             document_id IN (
                 SELECT id FROM documents 
                 WHERE user_id = auth.uid()
             )) OR
            -- Archive vectors
            (metadata->>'source_type' = 'thread_archive' AND
             metadata->>'user_id' = auth.uid()::text)
        )
    );

CREATE POLICY "Users can insert own vector chunks" ON vector_chunks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own vector chunks" ON vector_chunks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own vector chunks" ON vector_chunks
    FOR DELETE USING (auth.uid() = user_id);
```

#### Conversations RLS with Thread Isolation
```sql
-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Conversation policies with thread scoping
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads 
            WHERE user_id = auth.uid() AND status = 'active'
        )
    );

CREATE POLICY "Users can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own conversations" ON conversations
    FOR UPDATE USING (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own conversations" ON conversations
    FOR DELETE USING (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads 
            WHERE user_id = auth.uid()
        )
    );
```

### 2. Archive Retention Policies

#### Archive-Specific RLS
```sql
-- Special policy for archive vectors
CREATE POLICY "Users can access own archives" ON vector_chunks
    FOR SELECT USING (
        auth.uid()::text = metadata->>'user_id' AND
        metadata->>'source_type' = 'thread_archive'
    );

-- Archive retention policy (keep for 7 years)
CREATE POLICY "Archive retention policy" ON vector_chunks
    FOR DELETE USING (
        metadata->>'source_type' = 'thread_archive' AND
        (metadata->>'archived_at')::timestamp < NOW() - INTERVAL '7 years'
    );
```

#### Archive Management Functions
```sql
-- Function to clean old archives
CREATE OR REPLACE FUNCTION cleanup_old_archives()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM vector_chunks
    WHERE metadata->>'source_type' = 'thread_archive'
      AND (metadata->>'archived_at')::timestamp < NOW() - INTERVAL '7 years';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Scheduled cleanup (run monthly)
-- Add to cron job: SELECT cleanup_old_archives();
```

### 3. Multi-Thread Privacy Controls

#### Thread Isolation Functions
```sql
-- Function to verify thread ownership
CREATE OR REPLACE FUNCTION verify_thread_ownership(
    p_thread_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM threads 
        WHERE id = p_thread_id AND user_id = p_user_id
    );
END;
$$;

-- Function to get user's accessible threads
CREATE OR REPLACE FUNCTION get_user_threads(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    title TEXT,
    status TEXT,
    last_activity_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT t.id, t.title, t.status, t.last_activity_at
    FROM threads t
    WHERE t.user_id = p_user_id
    ORDER BY t.last_activity_at DESC;
END;
$$;
```

#### Cross-Thread Search Security
```sql
-- Secure cross-thread search function
CREATE OR REPLACE FUNCTION secure_cross_thread_search(
    query_embedding VECTOR(1536),
    p_user_id UUID,
    p_thread_ids UUID[] DEFAULT NULL,
    match_threshold FLOAT DEFAULT 0.8,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    thread_id UUID
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Verify user owns all specified threads
    IF p_thread_ids IS NOT NULL THEN
        IF NOT (
            SELECT bool_and(verify_thread_ownership(thread_id, p_user_id))
            FROM unnest(p_thread_ids) AS thread_id
        ) THEN
            RAISE EXCEPTION 'Access denied: User does not own all specified threads';
        END IF;
    END IF;

    RETURN QUERY
    SELECT
        vc.id,
        vc.content,
        vc.metadata,
        1 - (vc.embedding <=> query_embedding) AS similarity,
        (vc.metadata->>'thread_id')::UUID AS thread_id
    FROM vector_chunks vc
    WHERE vc.user_id = p_user_id
        AND (p_thread_ids IS NULL OR (vc.metadata->>'thread_id')::UUID = ANY(p_thread_ids))
        AND 1 - (vc.embedding <=> query_embedding) > match_threshold
    ORDER BY vc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

## 📊 Performance Monitoring and Optimization

### 1. Vector Performance Monitoring

#### Query Performance Tracking
```sql
-- Monitor vector search performance
CREATE TABLE vector_search_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    query_length INTEGER,
    result_count INTEGER,
    search_time_ms INTEGER,
    similarity_threshold FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to log search performance
CREATE OR REPLACE FUNCTION log_vector_search(
    p_user_id UUID,
    p_query_length INTEGER,
    p_result_count INTEGER,
    p_search_time_ms INTEGER,
    p_similarity_threshold FLOAT
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO vector_search_logs (
        user_id, query_length, result_count, 
        search_time_ms, similarity_threshold
    ) VALUES (
        p_user_id, p_query_length, p_result_count,
        p_search_time_ms, p_similarity_threshold
    );
END;
$$;
```

#### Performance Analytics
```sql
-- Average search performance by user
SELECT 
    user_id,
    COUNT(*) as search_count,
    AVG(search_time_ms) as avg_search_time,
    AVG(result_count) as avg_results,
    AVG(similarity_threshold) as avg_threshold
FROM vector_search_logs
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY user_id
ORDER BY search_count DESC;

-- Index performance monitoring
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    CASE 
        WHEN idx_scan > 0 THEN 
            ROUND((idx_tup_fetch::float / idx_tup_read::float) * 100, 2)
        ELSE 0 
    END as hit_ratio
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%vector%'
ORDER BY idx_scan DESC;
```

### 2. Storage Optimization

#### Vector Compression
```sql
-- Enable compression for vector metadata
ALTER TABLE vector_chunks ALTER COLUMN metadata SET COMPRESSION lz4;

-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                   pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Partitioning for Large Datasets
```sql
-- Partition vector_chunks by user_id for very large datasets
CREATE TABLE vector_chunks_partitioned (
    LIKE vector_chunks INCLUDING ALL
) PARTITION BY HASH (user_id);

-- Create partitions (example for 4 partitions)
CREATE TABLE vector_chunks_p0 PARTITION OF vector_chunks_partitioned
    FOR VALUES WITH (modulus 4, remainder 0);
CREATE TABLE vector_chunks_p1 PARTITION OF vector_chunks_partitioned
    FOR VALUES WITH (modulus 4, remainder 1);
CREATE TABLE vector_chunks_p2 PARTITION OF vector_chunks_partitioned
    FOR VALUES WITH (modulus 4, remainder 2);
CREATE TABLE vector_chunks_p3 PARTITION OF vector_chunks_partitioned
    FOR VALUES WITH (modulus 4, remainder 3);
```

## 🔧 Implementation Guidelines

### 1. Edge Function Best Practices

#### Optimized Vector Search
```typescript
// Optimized vector search in Edge Functions
export async function performVectorSearch(
  queryEmbedding: number[],
  userId: string,
  threadId?: string,
  options: {
    threshold: number;
    limit: number;
    includeArchives: boolean;
  } = { threshold: 0.7, limit: 5, includeArchives: false }
) {
  const startTime = Date.now();
  
  try {
    const { data, error } = await supabase.rpc('match_documents_optimized', {
      query_embedding: queryEmbedding,
      match_threshold: options.threshold,
      match_count: options.limit,
      p_user_id: userId,
      p_thread_id: threadId
    });

    if (error) throw error;

    // Log performance
    const searchTime = Date.now() - startTime;
    await supabase.rpc('log_vector_search', {
      p_user_id: userId,
      p_query_length: queryEmbedding.length,
      p_result_count: data?.length || 0,
      p_search_time_ms: searchTime,
      p_similarity_threshold: options.threshold
    });

    return data;
  } catch (error) {
    console.error('Vector search error:', error);
    throw error;
  }
}
```

#### Batch Processing
```typescript
// Efficient batch processing for vectorization
export async function processDocumentInBatches(
  content: string,
  documentId: string,
  userId: string,
  batchSize: number = 50
) {
  const chunks = await splitTextIntoChunks(content);
  const vectors = await generateEmbeddings(chunks);
  
  // Process in batches
  for (let i = 0; i < vectors.length; i += batchSize) {
    const batch = vectors.slice(i, i + batchSize).map((vector, index) => ({
      document_id: documentId,
      user_id: userId,
      content: chunks[i + index],
      embedding: vector,
      chunk_index: i + index,
      metadata: { thread_id: documentId }
    }));

    const { error } = await supabase
      .from('vector_chunks')
      .insert(batch);

    if (error) {
      console.error(`Batch ${i / batchSize + 1} failed:`, error);
      throw error;
    }
  }
}
```

### 2. Security Best Practices

#### Input Validation
```typescript
// Comprehensive input validation
export function validateVectorSearchInput(input: any) {
  const errors: string[] = [];
  
  if (!input.userId || typeof input.userId !== 'string') {
    errors.push('Valid userId required');
  }
  
  if (!input.query || typeof input.query !== 'string') {
    errors.push('Valid query required');
  }
  
  if (input.threshold && (input.threshold < 0 || input.threshold > 1)) {
    errors.push('Threshold must be between 0 and 1');
  }
  
  if (input.limit && (input.limit < 1 || input.limit > 100)) {
    errors.push('Limit must be between 1 and 100');
  }
  
  if (errors.length > 0) {
    throw new Error(`Validation errors: ${errors.join(', ')}`);
  }
  
  return true;
}
```

#### Rate Limiting
```typescript
// Rate limiting for vector operations
export async function checkRateLimit(userId: string, operation: string) {
  const key = `rate_limit:${userId}:${operation}`;
  const limit = operation === 'vector_search' ? 100 : 10; // per hour
  const window = 3600; // 1 hour in seconds
  
  const current = await redis.incr(key);
  if (current === 1) {
    await redis.expire(key, window);
  }
  
  if (current > limit) {
    throw new Error(`Rate limit exceeded for ${operation}`);
  }
  
  return true;
}
```

## 📈 Scaling Recommendations

### 1. Lab-Scale Data (< 1M vectors)
- **Index Type**: IVFFlat with 50-100 lists
- **Batch Size**: 50-100 vectors per batch
- **Connection Pool**: 5-10 connections
- **Monitoring**: Basic performance logging

### 2. Production-Scale Data (1M-10M vectors)
- **Index Type**: IVFFlat with 100-200 lists or HNSW
- **Batch Size**: 100-200 vectors per batch
- **Connection Pool**: 10-20 connections
- **Monitoring**: Comprehensive performance tracking
- **Partitioning**: Consider user-based partitioning

### 3. Enterprise-Scale Data (> 10M vectors)
- **Index Type**: HNSW with optimized parameters
- **Batch Size**: 200+ vectors per batch
- **Connection Pool**: 20+ connections
- **Monitoring**: Real-time performance analytics
- **Partitioning**: Implement table partitioning
- **Caching**: Redis caching for frequent queries

### 4. Archive Management
- **Retention**: 7-year archive retention
- **Compression**: LZ4 compression for metadata
- **Cleanup**: Automated monthly cleanup
- **Search**: Include archives in cross-thread search

This comprehensive guide ensures optimal performance, security, and scalability for your RAG application while maintaining user privacy and data integrity. 