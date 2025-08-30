# Edge Function Logging Guide

## Overview

This guide explains the comprehensive logging system implemented in the Supabase Edge Functions for debugging, monitoring, and performance tracking. The logging system provides detailed insights into each step of the vectorization process.

## Logging Architecture

### 1. Structured Logging Format

All logs follow a consistent format with prefixes for easy filtering and identification:

```
[COMPONENT] Message with details
```

### 2. Log Levels and Categories

- **🚀 [EDGE FUNCTION]**: Main request handling and routing
- **📄 [DOCUMENT VECTORIZATION]**: Document processing steps
- **💬 [CHAT HISTORY VECTORIZATION]**: Chat history processing steps
- **🔧 [EMBEDDING BATCHES]**: OpenAI embedding generation
- **💾 [DATABASE BATCHES]**: Database insertion operations
- **📝 [CHAT CHUNKS]**: Chat conversation chunking

### 3. Performance Tracking

Each operation includes timing information:
- Request start/end times
- Batch processing times
- Individual operation durations
- Performance summaries

## Logging Examples

### Document Vectorization Flow

```typescript
// Request received
[EDGE FUNCTION] 🚀 Vectorization request received: POST /functions/v1/vectorize
[EDGE FUNCTION] Verifying authentication...
[EDGE FUNCTION] ✅ Authentication successful for user: 123e4567-e89b-12d3-a456-426614174000
[EDGE FUNCTION] Processing document vectorization for user 123e4567-e89b-12d3-a456-426614174000
[EDGE FUNCTION] 📄 Starting document vectorization for document abc-123

// Document processing
[DOCUMENT VECTORIZATION] Starting vectorization for document abc-123, user 123e4567-e89b-12d3-a456-426614174000
[DOCUMENT VECTORIZATION] Fetching document content from database...
[DOCUMENT VECTORIZATION] Document found: "Research Paper" (15000 characters)
[DOCUMENT VECTORIZATION] Configuration: { chunkSize: 1000, chunkOverlap: 200, maxChunks: 1000, batchSize: 100, contentLength: 15000 }
[DOCUMENT VECTORIZATION] Creating text splitter...
[DOCUMENT VECTORIZATION] Splitting document into chunks...
[DOCUMENT VECTORIZATION] Document split into 15 chunks
[DOCUMENT VECTORIZATION] Processing 15 chunks (15 total)

// Embedding generation
[DOCUMENT VECTORIZATION] Starting embedding generation in batches of 50...
[EMBEDDING BATCHES] Starting batch processing for 15 texts in batches of 50
[EMBEDDING BATCHES] Processing batch 1/1 (15 texts)
[DOCUMENT VECTORIZATION] Processing embedding batch 1/1 (15 chunks)
[DOCUMENT VECTORIZATION] Batch 1 completed in 2500ms
[DOCUMENT VECTORIZATION] All embeddings generated successfully (15 total)
[EMBEDDING BATCHES] ✅ All batches completed successfully (15 embeddings)

// Database insertion
[DOCUMENT VECTORIZATION] Preparing vector chunks for database insertion...
[DOCUMENT VECTORIZATION] Prepared 15 vector chunks for insertion
[DOCUMENT VECTORIZATION] Starting database insertion in batches of 100...
[DATABASE BATCHES] Starting batch insertion for 15 chunks in batches of 100
[DATABASE BATCHES] Inserting batch 1/1 (15 chunks)
[DOCUMENT VECTORIZATION] Inserting batch 1/1 (15 chunks)
[DOCUMENT VECTORIZATION] Batch 1 inserted successfully in 150ms (15/15 total)
[DATABASE BATCHES] ✅ All batches inserted successfully (15 total)

// Completion
[DOCUMENT VECTORIZATION] Updating document status to completed...
[DOCUMENT VECTORIZATION] ✅ Document vectorization completed successfully!
[DOCUMENT VECTORIZATION] 📊 Summary: { documentId: "abc-123", userId: "123e4567-e89b-12d3-a456-426614174000", totalTime: "2650ms", processedChunks: 15, totalChunks: 15, insertedCount: 15, averageTimePerChunk: "177ms" }

[EDGE FUNCTION] 📊 Request completed in 2700ms: { type: "document", userId: "123e4567-e89b-12d3-a456-426614174000", success: true, vectorCount: 15, processedChunks: 15, totalChunks: 15 }
```

### Chat History Vectorization Flow

```typescript
// Request received
[EDGE FUNCTION] 🚀 Vectorization request received: POST /functions/v1/vectorize
[EDGE FUNCTION] 💬 Starting chat history vectorization for thread thread-456

// Chat processing
[CHAT HISTORY VECTORIZATION] Starting chat history vectorization for thread thread-456, user 123e4567-e89b-12d3-a456-426614174000
[CHAT HISTORY VECTORIZATION] Fetching chat history from database...
[CHAT HISTORY VECTORIZATION] Found 25 conversations in thread
[CHAT HISTORY VECTORIZATION] Creating chat chunks...
[CHAT CHUNKS] Creating chunks from 25 conversations
[CHAT CHUNKS] Grouped conversations into 8 time-based groups
[CHAT CHUNKS] Created 8 meaningful chunks from 8 groups
[CHAT HISTORY VECTORIZATION] Created 8 chat chunks
[CHAT HISTORY VECTORIZATION] Processing 8 chat chunks (8 total)

// Embedding generation
[CHAT HISTORY VECTORIZATION] Starting embedding generation for chat chunks...
[EMBEDDING BATCHES] Starting batch processing for 8 texts in batches of 50
[EMBEDDING BATCHES] Processing batch 1/1 (8 texts)
[EMBEDDING BATCHES] Batch 1 completed in 1200ms
[EMBEDDING BATCHES] ✅ All batches completed successfully (8 embeddings)

// Database insertion
[CHAT HISTORY VECTORIZATION] Prepared 8 vector chunks for insertion
[CHAT HISTORY VECTORIZATION] Starting database insertion in batches of 100...
[DATABASE BATCHES] Starting batch insertion for 8 chunks in batches of 100
[DATABASE BATCHES] Inserting batch 1/1 (8 chunks)
[DATABASE BATCHES] ✅ All batches inserted successfully (8 total)

// Completion
[CHAT HISTORY VECTORIZATION] ✅ Chat history vectorization completed successfully!
[CHAT HISTORY VECTORIZATION] 📊 Summary: { threadId: "thread-456", userId: "123e4567-e89b-12d3-a456-426614174000", totalTime: "1350ms", conversations: 25, processedChunks: 8, totalChunks: 8, insertedCount: 8, averageTimePerChunk: "169ms" }
```

## Error Logging

### Authentication Errors
```typescript
[EDGE FUNCTION] ❌ No authorization header provided
[EDGE FUNCTION] ❌ Authentication failed: Invalid JWT token
[EDGE FUNCTION] ❌ Unauthorized access: requested user 456 != authenticated user 123
```

### Processing Errors
```typescript
[DOCUMENT VECTORIZATION] ❌ Document vectorization failed after 1500ms: OpenAI API rate limit exceeded
[EMBEDDING BATCHES] ❌ Batch 2 error: Network timeout
[DATABASE BATCHES] ❌ Batch 1 insertion error: Connection pool exhausted
```

### Validation Errors
```typescript
[EDGE FUNCTION] ❌ Missing required fields: { type: undefined, userId: "123" }
[EDGE FUNCTION] ❌ Missing documentId for document vectorization
[EDGE FUNCTION] ❌ Invalid vectorization type: invalid_type
```

## Performance Monitoring

### Timing Breakdown
```typescript
// Request-level timing
[EDGE FUNCTION] 📊 Request completed in 2700ms: { ... }

// Operation-level timing
[DOCUMENT VECTORIZATION] 📊 Summary: { 
  totalTime: "2650ms",
  averageTimePerChunk: "177ms"
}

// Batch-level timing
[EMBEDDING BATCHES] Batch 1 completed in 2500ms
[DATABASE BATCHES] Batch 1 inserted successfully in 150ms
```

### Resource Usage Tracking
```typescript
// Memory and processing stats
[DOCUMENT VECTORIZATION] Configuration: { 
  chunkSize: 1000, 
  chunkOverlap: 200, 
  maxChunks: 1000, 
  batchSize: 100, 
  contentLength: 15000 
}

// Processing statistics
[DOCUMENT VECTORIZATION] Processing 15 chunks (15 total)
[CHAT HISTORY VECTORIZATION] Processing 8 chat chunks (8 total)
```

## Debugging with Logs

### 1. Performance Issues
```bash
# Filter for timing information
grep "completed in" supabase-functions.log
grep "📊 Summary" supabase-functions.log

# Find slow operations
grep "Batch.*completed in [0-9]{4,}ms" supabase-functions.log
```

### 2. Error Investigation
```bash
# Find all errors
grep "❌" supabase-functions.log

# Find specific error types
grep "Authentication failed" supabase-functions.log
grep "OpenAI API" supabase-functions.log
grep "Database.*error" supabase-functions.log
```

### 3. Request Tracking
```bash
# Track specific document processing
grep "document abc-123" supabase-functions.log

# Track specific user activity
grep "user 123e4567-e89b-12d3-a456-426614174000" supabase-functions.log

# Track specific thread processing
grep "thread thread-456" supabase-functions.log
```

### 4. Batch Processing Monitoring
```bash
# Monitor embedding batches
grep "\[EMBEDDING BATCHES\]" supabase-functions.log

# Monitor database batches
grep "\[DATABASE BATCHES\]" supabase-functions.log

# Monitor progress
grep "Batch.*\/.*" supabase-functions.log
```

## Log Analysis Tools

### 1. Supabase Dashboard
- View real-time logs in Supabase Dashboard
- Filter by function name and time range
- Search for specific error patterns

### 2. Command Line Analysis
```bash
# Count successful vs failed requests
grep "✅" supabase-functions.log | wc -l
grep "❌" supabase-functions.log | wc -l

# Average processing time
grep "📊 Summary" supabase-functions.log | grep -o "totalTime: \"[0-9]*ms\"" | grep -o "[0-9]*" | awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'

# Most common errors
grep "❌" supabase-functions.log | cut -d':' -f3- | sort | uniq -c | sort -nr
```

### 3. Performance Monitoring
```bash
# Monitor processing times
grep "📊 Summary" supabase-functions.log | grep -o "totalTime: \"[0-9]*ms\"" | grep -o "[0-9]*" | sort -n

# Find outliers (slow requests)
grep "📊 Summary" supabase-functions.log | grep -o "totalTime: \"[0-9]*ms\"" | grep -o "[0-9]*" | awk '$1 > 10000 {print "Slow request:", $1, "ms"}'
```

## Best Practices

### 1. Log Management
- **Rotate logs**: Implement log rotation to prevent disk space issues
- **Archive logs**: Store historical logs for trend analysis
- **Monitor log size**: Set up alerts for log file size

### 2. Performance Monitoring
- **Set thresholds**: Define acceptable processing times
- **Track trends**: Monitor performance over time
- **Alert on anomalies**: Set up alerts for unusual patterns

### 3. Error Handling
- **Categorize errors**: Group similar errors for analysis
- **Track error rates**: Monitor error frequency
- **Implement retries**: Add retry logic for transient failures

### 4. Security
- **Sanitize logs**: Remove sensitive information from logs
- **Access control**: Limit log access to authorized personnel
- **Audit trails**: Maintain logs for security auditing

## Troubleshooting Common Issues

### 1. High Processing Times
```bash
# Check for slow embedding generation
grep "Batch.*completed in [0-9]{4,}ms" supabase-functions.log | grep "EMBEDDING"

# Check for slow database operations
grep "Batch.*inserted successfully in [0-9]{4,}ms" supabase-functions.log
```

### 2. Memory Issues
```bash
# Check for large documents
grep "contentLength: [0-9]{5,}" supabase-functions.log

# Check for excessive chunking
grep "Document split into [0-9]{3,} chunks" supabase-functions.log
```

### 3. API Rate Limits
```bash
# Check for rate limit errors
grep "rate limit" supabase-functions.log
grep "OpenAI API" supabase-functions.log | grep "error"
```

### 4. Database Issues
```bash
# Check for database errors
grep "DATABASE BATCHES.*error" supabase-functions.log
grep "Batch insertion failed" supabase-functions.log
```

## Conclusion

The comprehensive logging system provides:
- ✅ **Detailed tracking** of every processing step
- ✅ **Performance monitoring** with timing information
- ✅ **Error identification** with clear error messages
- ✅ **Debugging support** for troubleshooting issues
- ✅ **Resource monitoring** for optimization
- ✅ **Security auditing** for compliance

This logging system enables effective debugging, performance optimization, and operational monitoring of the vectorization Edge Functions. 