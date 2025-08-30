# RAG Query System Guide

## Overview

This guide explains the comprehensive RAG (Retrieval-Augmented Generation) query system implemented in the Supabase Edge Function. The system provides enhanced similarity search, contextual responses, and chat history management for multi-thread conversations.

## Key Features

### 1. Enhanced Similarity Search
- **Vector-based retrieval**: Uses OpenAI embeddings for semantic search
- **Source weighting**: Different weights for documents, chat history, and thread archives
- **Similarity filtering**: Configurable similarity thresholds
- **Thread scoping**: Search within specific threads or across all user content

### 2. Contextual Response Generation
- **Thread context**: Includes thread information in responses
- **Source attribution**: References specific sources in responses
- **Model flexibility**: Support for different OpenAI models
- **Token tracking**: Monitor token usage for cost optimization

### 3. Chat History Management
- **Automatic saving**: Saves queries and responses to conversation history
- **Thread isolation**: Each thread maintains separate conversation history
- **Vectorization support**: Chat history can be vectorized for future recall
- **Multi-thread support**: Users can have multiple independent threads

## API Endpoint

### URL
```
POST /functions/v1/rag-query
```

### Request Format
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
}
```

### Response Format
```typescript
interface RAGQueryResponse {
  success: boolean
  response?: string
  sources?: Array<{
    content: string
    metadata: Record<string, any>
    similarity: number
    sourceType: 'document' | 'chat_history' | 'thread_archive'
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
  error?: string
}
```

## Usage Examples

### Basic RAG Query
```typescript
const response = await fetch('/functions/v1/rag-query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    threadId: 'thread-123',
    userId: 'user-456',
    query: 'What are the main points in the uploaded documents?'
  })
});

const result = await response.json();
console.log('Response:', result.response);
console.log('Sources:', result.sources);
```

### Advanced RAG Query with Options
```typescript
const response = await fetch('/functions/v1/rag-query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    threadId: 'thread-123',
    userId: 'user-456',
    query: 'Summarize our previous discussion about the project',
    maxResults: 10,
    includeChatHistory: true,
    includeThreadContext: true,
    temperature: 0.5,
    model: 'gpt-4-turbo'
  })
});

const result = await response.json();
console.log('Thread Context:', result.threadContext);
console.log('Performance:', result.performance);
```

## Configuration

### RAG Configuration Constants
```typescript
const RAG_CONFIG = {
  DEFAULT_MAX_RESULTS: 8,
  DEFAULT_TEMPERATURE: 0.7,
  DEFAULT_MODEL: 'gpt-4',
  MAX_TOKENS: 2000,
  SIMILARITY_THRESHOLD: 0.7,
  CONTEXT_WINDOW_SIZE: 4000,
  CHAT_HISTORY_WEIGHT: 0.8,
  DOCUMENT_WEIGHT: 1.0,
  THREAD_ARCHIVE_WEIGHT: 0.9,
}
```

### Source Weighting
- **Documents**: Weight 1.0 (highest priority)
- **Thread Archives**: Weight 0.9 (high priority)
- **Chat History**: Weight 0.8 (medium priority)

## Processing Flow

### 1. Request Validation
```typescript
// Verify authentication
// Validate required fields
// Check thread ownership
// Verify thread exists
```

### 2. Thread Context Retrieval
```typescript
// Fetch thread information
// Get conversation count
// Retrieve last activity timestamp
```

### 3. Query Embedding Generation
```typescript
// Generate OpenAI embedding for user query
// Track embedding generation time
```

### 4. Similarity Search
```typescript
// Perform vector similarity search
// Apply thread filtering
// Filter by chat history inclusion
// Calculate similarity scores
// Apply similarity threshold
// Weight by source type
// Sort by weighted relevance
```

### 5. Context Preparation
```typescript
// Sort chunks by weighted relevance
// Add source information
// Truncate to context window size
// Prepare for prompt generation
```

### 6. Response Generation
```typescript
// Create enhanced prompt with thread context
// Generate response with OpenAI
// Track token usage
// Monitor generation time
```

### 7. Conversation Saving
```typescript
// Save user query to database
// Save AI response to database
// Update thread activity timestamp
// Return conversation IDs
```

## Logging and Monitoring

### Request-Level Logging
```typescript
[RAG EDGE FUNCTION] 🚀 RAG query request received: POST /functions/v1/rag-query
[RAG EDGE FUNCTION] ✅ Authentication successful for user: user-456
[RAG EDGE FUNCTION] Processing RAG query for thread thread-123
[RAG EDGE FUNCTION] ✅ Thread access verified
```

### Processing-Level Logging
```typescript
[RAG QUERY] 🚀 Starting RAG query for thread thread-123, user user-456
[RAG QUERY] Query: "What are the main points in the uploaded documents?"
[RAG QUERY] Fetching thread context...
[RAG QUERY] Generating query embedding...
[RAG QUERY] Query embedding generated in 250ms
[RAG QUERY] Performing similarity search...
[RAG QUERY] Similarity search completed in 150ms, found 8 chunks
```

### Performance Monitoring
```typescript
[RAG QUERY] 📊 Performance: {
  searchTime: 150,
  generationTime: 2500,
  totalTime: 2700,
  tokensUsed: 1250,
  chunksFound: 8,
  sourcesReturned: 8
}
```

## Error Handling

### Authentication Errors
```typescript
[RAG EDGE FUNCTION] ❌ No authorization header provided
[RAG EDGE FUNCTION] ❌ Authentication failed: Invalid JWT token
[RAG EDGE FUNCTION] ❌ Unauthorized access: requested user 456 != authenticated user 123
```

### Validation Errors
```typescript
[RAG EDGE FUNCTION] ❌ Missing required fields: { threadId: undefined, userId: "123", query: "provided" }
[RAG EDGE FUNCTION] ❌ Thread not found or access denied: Row not found
```

### Processing Errors
```typescript
[RAG QUERY] ❌ RAG query failed after 1500ms: Similarity search failed: Database connection error
[RAG QUERY] ❌ RAG query failed after 3000ms: Failed to generate response: OpenAI API rate limit exceeded
```

## Best Practices

### 1. Query Optimization
- **Be specific**: Use detailed queries for better retrieval
- **Include context**: Reference previous conversations when relevant
- **Use keywords**: Include important terms from your documents

### 2. Thread Management
- **Create dedicated threads**: Use separate threads for different topics
- **Maintain context**: Keep related conversations in the same thread
- **Regular cleanup**: Archive old threads to improve performance

### 3. Performance Optimization
- **Monitor token usage**: Track costs and optimize prompt length
- **Adjust similarity threshold**: Lower for more results, higher for precision
- **Use appropriate models**: Choose models based on complexity and cost

### 4. Error Handling
- **Implement retries**: Handle transient API failures
- **Graceful degradation**: Provide fallback responses when search fails
- **User feedback**: Inform users when no relevant content is found

## Advanced Features

### 1. Hybrid Search Strategy
```typescript
// Combine semantic and keyword search
// Weight different search methods
// Merge and rank results
```

### 2. Structured Responses
```typescript
// Return JSON-structured responses
// Include confidence scores
// Provide multiple answer candidates
```

### 3. Conversation Memory
```typescript
// Maintain conversation context
// Reference previous exchanges
// Build on ongoing discussions
```

### 4. Multi-Modal Support
```typescript
// Support for images and documents
// Extract text from various formats
// Handle different content types
```

## Troubleshooting

### Common Issues

1. **No Results Found**
   - Check if documents are vectorized
   - Verify thread filtering is correct
   - Lower similarity threshold
   - Ensure chat history is included if needed

2. **Slow Response Times**
   - Monitor embedding generation time
   - Check database query performance
   - Optimize context window size
   - Use faster models for simple queries

3. **High Token Usage**
   - Reduce context window size
   - Limit number of results
   - Use more concise prompts
   - Monitor token usage patterns

4. **Authentication Issues**
   - Verify JWT token is valid
   - Check user permissions
   - Ensure thread ownership
   - Validate request format

### Debug Mode
```typescript
// Enable detailed logging
// Monitor each processing step
// Track performance metrics
// Identify bottlenecks
```

## Integration Examples

### Frontend Integration
```typescript
// React component for RAG queries
const RAGQueryComponent = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    setLoading(true);
    try {
      const result = await performRAGQuery({
        threadId: currentThread.id,
        userId: user.id,
        query,
        includeChatHistory: true,
        includeThreadContext: true
      });
      
      if (result.success) {
        setResponse(result.response);
        console.log('Sources:', result.sources);
        console.log('Performance:', result.performance);
      }
    } catch (error) {
      console.error('RAG query failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <button onClick={handleQuery} disabled={loading}>
        {loading ? 'Querying...' : 'Ask'}
      </button>
      {response && <div>{response}</div>}
    </div>
  );
};
```

### Backend Integration
```typescript
// Node.js server integration
app.post('/api/rag-query', async (req, res) => {
  try {
    const { threadId, userId, query, options } = req.body;
    
    const result = await fetch(`${SUPABASE_URL}/functions/v1/rag-query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        threadId,
        userId,
        query,
        ...options
      })
    });

    const ragResult = await result.json();
    res.json(ragResult);
  } catch (error) {
    res.status(500).json({ error: 'RAG query failed' });
  }
});
```

## Conclusion

The RAG query system provides:
- ✅ **Enhanced similarity search** with source weighting
- ✅ **Contextual responses** with thread awareness
- ✅ **Chat history management** for multi-thread support
- ✅ **Performance monitoring** with detailed metrics
- ✅ **Comprehensive logging** for debugging
- ✅ **Flexible configuration** for different use cases
- ✅ **Robust error handling** with graceful degradation

This system enables powerful, context-aware conversations with your vectorized documents and chat history. 