# Retrieval Filtering Guide

## Overview

This guide explains the enhanced retrieval filtering system implemented in the RAG query function. The system provides intelligent top-k retrieval from user/thread-specific vectors across multiple threads, enabling more relevant and context-aware search results.

## Key Features

### 1. Top-K Retrieval per Thread
- **Configurable limits**: Set number of top chunks per thread (default: 3)
- **Thread-specific search**: Search within each thread independently
- **Quality filtering**: Apply similarity thresholds per thread
- **Weighted ranking**: Combine similarity scores with source weights

### 2. Cross-Thread Search
- **Multi-thread exploration**: Search across user's threads (default: 5 threads)
- **Thread prioritization**: Prioritize current thread vs. other threads
- **Configurable scope**: Enable/disable cross-thread search
- **Smart weighting**: Different weights for current vs. cross-thread results

### 3. Enhanced Filtering
- **Similarity thresholds**: Different thresholds for current vs. cross-thread
- **Source type weighting**: Documents, chat history, thread archives
- **User isolation**: Strict user-based filtering for security
- **Thread isolation**: Respect thread boundaries and permissions

## Configuration

### Retrieval Configuration Constants
```typescript
const RAG_CONFIG = {
  // Basic settings
  DEFAULT_MAX_RESULTS: 8,
  SIMILARITY_THRESHOLD: 0.7,
  
  // Retrieval filtering configuration
  TOP_K_PER_THREAD: 3, // Number of top chunks per thread
  MAX_THREADS_SEARCH: 5, // Maximum number of threads to search
  CROSS_THREAD_WEIGHT: 0.9, // Weight for cross-thread results
  CURRENT_THREAD_WEIGHT: 1.0, // Weight for current thread results
  MIN_SIMILARITY_CROSS_THREAD: 0.8, // Higher threshold for cross-thread results
}
```

### Request Options
```typescript
interface RAGQueryRequest {
  // Basic options
  threadId: string
  userId: string
  query: string
  maxResults?: number
  
  // Retrieval filtering options
  topKPerThread?: number
  maxThreadsSearch?: number
  crossThreadSearch?: boolean
  currentThreadPriority?: boolean
}
```

## Usage Examples

### Basic Top-K Retrieval
```typescript
const result = await performRAGQuery(threadId, userId, query, {
  topKPerThread: 3,
  maxThreadsSearch: 5,
  crossThreadSearch: true,
  currentThreadPriority: true
});
```

### Single Thread Search
```typescript
const result = await performRAGQuery(threadId, userId, query, {
  crossThreadSearch: false, // Search only current thread
  topKPerThread: 5 // Get more results from single thread
});
```

### Cross-Thread Search with Equal Priority
```typescript
const result = await performRAGQuery(threadId, userId, query, {
  crossThreadSearch: true,
  currentThreadPriority: false, // Equal priority for all threads
  maxThreadsSearch: 10 // Search more threads
});
```

### Aggressive Cross-Thread Search
```typescript
const result = await performRAGQuery(threadId, userId, query, {
  topKPerThread: 2, // Fewer per thread
  maxThreadsSearch: 8, // More threads
  crossThreadSearch: true,
  currentThreadPriority: false
});
```

## Processing Flow

### 1. Thread Discovery
```typescript
// Get user's threads for cross-thread search
const { data: userThreads } = await supabase
  .from('threads')
  .select('id, title, created_at')
  .eq('user_id', request.userId)
  .order('updated_at', { ascending: false })
  .limit(maxThreadsSearch)
```

### 2. Per-Thread Search
```typescript
for (const thread of threadsToSearch) {
  // Build similarity search query for this thread
  let threadQuery = supabase
    .from('vector_chunks')
    .select('content, metadata, embedding, thread_id')
    .eq('user_id', request.userId)
    .eq('thread_id', thread.id)
    .order(`embedding <-> '[${queryEmbedding.join(',')}]'::vector`, { ascending: true })
    .limit(topKPerThread * 2) // Get more for filtering

  // Execute search and process results
  const { data: threadChunks } = await threadQuery
  // Calculate similarity scores and apply filtering
}
```

### 3. Similarity Scoring
```typescript
// Calculate similarity scores for this thread's chunks
const scoredChunks = threadChunks.map(chunk => ({
  ...chunk,
  similarity: calculateCosineSimilarity(queryEmbedding, chunk.embedding),
  threadId: thread.id,
  threadTitle: thread.title
}))

// Apply similarity threshold (higher for cross-thread results)
const threshold = thread.id === request.threadId 
  ? RAG_CONFIG.SIMILARITY_THRESHOLD 
  : RAG_CONFIG.MIN_SIMILARITY_CROSS_THREAD

const filteredChunks = scoredChunks.filter(chunk => chunk.similarity >= threshold)
```

### 4. Top-K Selection
```typescript
// Apply source type weighting
const weightedChunks = filteredChunks.map(chunk => ({
  ...chunk,
  weight: calculateSourceWeight(chunk.metadata)
}))

// Sort by weighted score and take top-k
const topKChunks = weightedChunks
  .sort((a, b) => (b.similarity * b.weight) - (a.similarity * a.weight))
  .slice(0, topKPerThread)
```

### 5. Cross-Thread Weighting
```typescript
// Apply cross-thread weighting based on priority settings
const crossThreadWeightedChunks = allChunks.map(chunk => {
  const isCurrentThread = chunk.threadId === request.threadId
  
  let threadWeight = RAG_CONFIG.CROSS_THREAD_WEIGHT
  if (isCurrentThread && currentThreadPriority) {
    threadWeight = RAG_CONFIG.CURRENT_THREAD_WEIGHT
  }

  return {
    ...chunk,
    finalWeight: chunk.weight * threadWeight,
    isCurrentThread
  }
})
```

### 6. Final Ranking
```typescript
// Sort by final weighted score and limit to max results
const finalResults = crossThreadWeightedChunks
  .sort((a, b) => (b.similarity * b.finalWeight) - (a.similarity * a.finalWeight))
  .slice(0, maxResults)
```

## Logging and Monitoring

### Search Configuration Logging
```typescript
console.log(`[RAG QUERY] Configuration:`, {
  maxResults,
  topKPerThread,
  maxThreadsSearch,
  crossThreadSearch,
  currentThreadPriority,
  currentThreadId: request.threadId
})
```

### Thread Search Progress
```typescript
console.log(`[RAG QUERY] Searching thread: ${thread.title} (${thread.id})`)
console.log(`[RAG QUERY] Thread ${thread.title}: ${topKChunks.length}/${threadChunks.length} chunks selected`)
```

### Final Results Summary
```typescript
console.log(`[RAG QUERY] Enhanced similarity search completed:`, {
  threadsSearched: threadResults.length,
  totalChunksFound: allChunks.length,
  finalResults: finalResults.length,
  currentThreadResults: currentThreadResults.length,
  crossThreadResults: crossThreadResults.length,
  averageSimilarity: finalResults.reduce((sum, chunk) => sum + chunk.similarity, 0) / finalResults.length,
  threadBreakdown: threadResults.map(r => ({
    thread: r.threadTitle,
    selected: r.chunks.length,
    total: r.totalChunks
  }))
})
```

## Performance Optimization

### 1. Query Optimization
- **Limit per thread**: Reduce database load with top-k limits
- **Thread filtering**: Use database indexes for efficient filtering
- **Batch processing**: Process threads sequentially to avoid overwhelming database

### 2. Memory Management
- **Streaming results**: Process chunks in batches
- **Early filtering**: Apply thresholds before full processing
- **Result limiting**: Limit final results to prevent memory issues

### 3. Caching Strategies
- **Thread metadata**: Cache thread information
- **Similarity scores**: Cache computed similarity scores
- **User permissions**: Cache user access rights

## Best Practices

### 1. Configuration Tuning
- **Start conservative**: Use lower top-k values initially
- **Monitor performance**: Track search times and result quality
- **Adjust thresholds**: Fine-tune similarity thresholds based on data

### 2. Thread Management
- **Limit thread count**: Don't search too many threads at once
- **Prioritize recent**: Focus on recently active threads
- **Respect boundaries**: Maintain thread isolation for security

### 3. Quality Control
- **Validate results**: Ensure results are relevant to query
- **Monitor diversity**: Balance current thread vs. cross-thread results
- **Track metrics**: Monitor similarity scores and result distribution

## Error Handling

### 1. Thread Access Errors
```typescript
if (threadError || !currentThread) {
  throw new Error(`Failed to fetch current thread: ${threadError?.message}`)
}
```

### 2. Search Errors
```typescript
if (threadSearchError) {
  console.error(`[RAG QUERY] Error searching thread ${thread.id}:`, threadSearchError)
  continue // Skip this thread and continue with others
}
```

### 3. Empty Results
```typescript
if (allChunks.length === 0) {
  console.warn(`[RAG QUERY] No relevant chunks found across all threads`)
  return []
}
```

## Advanced Features

### 1. Dynamic Thresholds
```typescript
// Adjust thresholds based on result availability
if (filteredChunks.length < topKPerThread) {
  // Lower threshold to get more results
  const lowerThreshold = threshold * 0.8
  const additionalChunks = scoredChunks.filter(chunk => 
    chunk.similarity >= lowerThreshold && chunk.similarity < threshold
  )
}
```

### 2. Thread Relevance Scoring
```typescript
// Score threads based on relevance to query
const threadScores = threadResults.map(result => ({
  threadId: result.threadId,
  threadTitle: result.threadTitle,
  relevanceScore: result.chunks.reduce((sum, chunk) => sum + chunk.similarity, 0) / result.chunks.length,
  chunkCount: result.chunks.length
}))
```

### 3. Adaptive Search
```typescript
// Adapt search strategy based on result quality
if (finalResults.length < maxResults * 0.5) {
  // Expand search if results are insufficient
  const expandedResults = await performExpandedSearch(request, queryEmbedding)
  finalResults.push(...expandedResults)
}
```

## Troubleshooting

### Common Issues

1. **Low Result Count**
   - Increase `topKPerThread`
   - Lower similarity thresholds
   - Enable cross-thread search
   - Check if documents are properly vectorized

2. **Poor Result Quality**
   - Increase similarity thresholds
   - Adjust source type weights
   - Review document chunking strategy
   - Check embedding quality

3. **Performance Issues**
   - Reduce `maxThreadsSearch`
   - Lower `topKPerThread`
   - Disable cross-thread search
   - Optimize database queries

4. **Memory Issues**
   - Reduce result limits
   - Implement pagination
   - Use streaming processing
   - Monitor memory usage

### Debug Mode
```typescript
// Enable detailed logging for debugging
console.log(`[RAG QUERY] Debug: Thread search details`, {
  threadId: thread.id,
  chunksFound: threadChunks.length,
  filteredCount: filteredChunks.length,
  topKSelected: topKChunks.length,
  averageSimilarity: topKChunks.reduce((sum, chunk) => sum + chunk.similarity, 0) / topKChunks.length
})
```

## Conclusion

The retrieval filtering system provides:
- ✅ **Intelligent top-k retrieval** from user/thread-specific vectors
- ✅ **Cross-thread search** with configurable scope and priority
- ✅ **Enhanced filtering** with similarity thresholds and source weighting
- ✅ **Performance optimization** through efficient query strategies
- ✅ **Comprehensive logging** for monitoring and debugging
- ✅ **Flexible configuration** for different use cases
- ✅ **Robust error handling** with graceful degradation

This system enables more relevant and context-aware search results while maintaining performance and security across multiple threads. 