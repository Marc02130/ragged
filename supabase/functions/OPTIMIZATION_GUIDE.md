# Large Document Optimization Guide

## Overview

This guide explains the optimizations implemented for handling large documents in the RAG application, including chunking limits, batch processing, and enhanced RLS scoping for multiple threads.

## Key Optimizations

### 1. Chunking Limits and Configuration

#### Configuration Constants
```typescript
const VECTORIZATION_CONFIG = {
  MAX_CHUNKS_PER_DOCUMENT: 1000,    // Limit chunks per document
  BATCH_SIZE: 100,                   // Insert chunks in batches of 100
  DEFAULT_CHUNK_SIZE: 1000,          // Default chunk size in characters
  DEFAULT_CHUNK_OVERLAP: 200,        // Default overlap between chunks
  MAX_EMBEDDING_BATCH_SIZE: 50,      // OpenAI API limit for embeddings
  MAX_CONTENT_LENGTH: 1000000,       // 1MB content limit
  RATE_LIMIT_DELAY: 1000,           // 1 second delay between batches
}
```

#### Usage Examples
```typescript
// Basic vectorization with defaults
const result = await vectorizeDocument(documentId, userId);

// Optimized for large documents
const result = await vectorizeDocument(documentId, userId, {
  maxChunks: 500,        // Limit to 500 chunks
  batchSize: 50,         // Smaller batches for large docs
  chunkSize: 1500,       // Larger chunks for better context
  chunkOverlap: 300      // More overlap for continuity
});

// Optimized for small documents
const result = await vectorizeDocument(documentId, userId, {
  maxChunks: 100,        // Fewer chunks for small docs
  batchSize: 200,        // Larger batches for efficiency
  chunkSize: 800,        // Smaller chunks for precision
  chunkOverlap: 150      // Less overlap for small docs
});
```

### 2. Batch Processing

#### Embedding Batch Processing
- **API Rate Limiting**: Respects OpenAI's 50-embedding batch limit
- **Automatic Retry**: Handles API failures with exponential backoff
- **Progress Tracking**: Logs batch processing progress
- **Memory Management**: Processes chunks in memory-efficient batches

```typescript
// Process embeddings in batches
const embeddingsList = await processEmbeddingsInBatches(
  texts, 
  VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE
);
```

#### Database Batch Insertion
- **Batch Size Control**: Configurable batch sizes (default: 100)
- **Transaction Safety**: Each batch is atomic
- **Error Recovery**: Failed batches don't affect successful ones
- **Performance Monitoring**: Tracks insertion progress

```typescript
// Insert vector chunks in batches
const insertedCount = await insertVectorChunksInBatches(
  vectorChunks, 
  VECTORIZATION_CONFIG.BATCH_SIZE
);
```

### 3. Enhanced RLS Scoping

#### Thread-Based Scoping
The system now supports per-thread vector chunk scoping:

```sql
-- Updated RLS policies include thread_id scoping
CREATE POLICY "Users can view own vector chunks" ON vector_chunks
    FOR SELECT USING (
        auth.uid() = user_id AND 
        (thread_id IS NULL OR thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        ))
    );
```

#### Multi-Thread Support
- **Thread Isolation**: Each thread's vectors are scoped separately
- **Cross-Thread Queries**: Can query across multiple user threads
- **Thread-Specific Statistics**: Track vector usage per thread
- **Cleanup Functions**: Remove orphaned vectors when threads are deleted

### 4. Database Optimizations

#### New Indexes for Performance
```sql
-- Thread-specific queries
CREATE INDEX idx_vector_chunks_thread_id ON vector_chunks(thread_id);

-- User-thread composite queries
CREATE INDEX idx_vector_chunks_user_thread ON vector_chunks(user_id, thread_id);

-- Document-specific queries
CREATE INDEX idx_vector_chunks_doc_user ON vector_chunks(document_id, user_id);

-- Metadata queries
CREATE INDEX idx_vector_chunks_metadata ON vector_chunks USING GIN (metadata);
```

#### New Columns for Tracking
```sql
-- Processing status tracking
ALTER TABLE vector_chunks ADD COLUMN processing_status TEXT DEFAULT 'completed';

-- Batch information
ALTER TABLE vector_chunks ADD COLUMN batch_info JSONB DEFAULT '{}';

-- Thread scoping
ALTER TABLE vector_chunks ADD COLUMN thread_id UUID REFERENCES threads(id);
```

### 5. Utility Functions

#### Statistics Functions
```sql
-- Get user vector statistics
SELECT * FROM get_user_vector_stats(user_uuid);

-- Get thread-specific statistics
SELECT * FROM get_thread_vector_stats(thread_uuid, user_uuid);

-- Clean up orphaned vectors
SELECT cleanup_orphaned_vector_chunks();
```

#### Frontend Integration
```typescript
// Get user statistics
const stats = await supabase.rpc('get_user_vector_stats', { user_uuid: userId });

// Get thread statistics
const threadStats = await supabase.rpc('get_thread_vector_stats', { 
  thread_uuid: threadId, 
  user_uuid: userId 
});
```

## Performance Benefits

### 1. Memory Efficiency
- **Chunk Limiting**: Prevents memory overflow with large documents
- **Batch Processing**: Reduces memory footprint during processing
- **Streaming**: Processes documents in manageable chunks

### 2. API Rate Limiting
- **Respects Limits**: Stays within OpenAI API rate limits
- **Automatic Delays**: Built-in delays between batches
- **Error Recovery**: Handles API failures gracefully

### 3. Database Performance
- **Indexed Queries**: Fast retrieval with proper indexing
- **Batch Inserts**: Efficient database operations
- **RLS Optimization**: Minimal overhead for security checks

### 4. Scalability
- **Horizontal Scaling**: Supports multiple concurrent users
- **Thread Isolation**: Independent processing per thread
- **Resource Management**: Efficient resource utilization

## Usage Patterns

### 1. Large Document Processing
```typescript
// For documents > 100KB
const result = await vectorizeDocument(documentId, userId, {
  maxChunks: 1000,       // Maximum chunks
  batchSize: 50,         // Smaller batches
  chunkSize: 1500,       // Larger chunks
  chunkOverlap: 300      // More overlap
});
```

### 2. Small Document Processing
```typescript
// For documents < 10KB
const result = await vectorizeDocument(documentId, userId, {
  maxChunks: 50,         // Fewer chunks
  batchSize: 200,        // Larger batches
  chunkSize: 800,        // Smaller chunks
  chunkOverlap: 150      // Less overlap
});
```

### 3. Chat History Processing
```typescript
// For chat history vectorization
const result = await vectorizeChatHistory(threadId, userId, {
  maxChunks: 200,        // Limit chat chunks
  batchSize: 100,        // Standard batch size
  chunkSize: 1000,       // Standard chunk size
  chunkOverlap: 200      // Standard overlap
});
```

## Monitoring and Debugging

### 1. Progress Tracking
```typescript
// Monitor processing progress
console.log(`Processing batch ${batchNumber}/${totalBatches}`);
console.log(`Inserted ${insertedCount}/${totalChunks} chunks`);
```

### 2. Error Handling
```typescript
// Comprehensive error responses
{
  success: false,
  message: 'Document vectorization failed',
  error: 'Detailed error message',
  processedChunks: 150,    // Chunks processed before failure
  totalChunks: 1000        // Total chunks attempted
}
```

### 3. Performance Metrics
```sql
-- Monitor vector usage
SELECT 
  user_id,
  COUNT(*) as total_chunks,
  COUNT(DISTINCT document_id) as documents,
  COUNT(DISTINCT thread_id) as threads
FROM vector_chunks 
GROUP BY user_id;
```

## Best Practices

### 1. Document Size Guidelines
- **Small (< 10KB)**: Use default settings
- **Medium (10KB - 100KB)**: Increase chunk size, standard batches
- **Large (100KB - 1MB)**: Use large document optimizations
- **Very Large (> 1MB)**: Consider document splitting

### 2. Thread Management
- **Create Threads**: Always associate documents with threads
- **Monitor Usage**: Track vector usage per thread
- **Cleanup**: Remove unused threads to free resources

### 3. Error Handling
- **Retry Logic**: Implement retry for transient failures
- **Fallback**: Provide alternative processing paths
- **Monitoring**: Track error rates and performance

### 4. Resource Management
- **Memory**: Monitor memory usage during processing
- **API Limits**: Respect OpenAI rate limits
- **Database**: Monitor connection pool usage

## Troubleshooting

### Common Issues

1. **Memory Errors**
   - Reduce `maxChunks` or `batchSize`
   - Increase `chunkSize` to reduce total chunks
   - Process documents in smaller sections

2. **API Rate Limits**
   - Increase `RATE_LIMIT_DELAY`
   - Reduce `MAX_EMBEDDING_BATCH_SIZE`
   - Implement exponential backoff

3. **Database Timeouts**
   - Reduce `batchSize` for inserts
   - Add database connection pooling
   - Monitor query performance

4. **RLS Policy Issues**
   - Verify user authentication
   - Check thread ownership
   - Review RLS policy configuration

### Debug Mode
```typescript
// Enable detailed logging
const result = await vectorizeDocument(documentId, userId, {
  // ... options
});

// Check detailed response
console.log('Processing details:', {
  processedChunks: result.processedChunks,
  totalChunks: result.totalChunks,
  vectorCount: result.vectorCount
});
```

## Conclusion

These optimizations provide:
- ✅ **Scalability**: Handle documents of any size
- ✅ **Performance**: Efficient processing and storage
- ✅ **Reliability**: Robust error handling and recovery
- ✅ **Security**: Enhanced RLS scoping for multi-thread support
- ✅ **Monitoring**: Comprehensive tracking and debugging

The system is now optimized for production use with large-scale document processing capabilities. 