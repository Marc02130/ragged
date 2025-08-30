# RAG Application Edge Functions

This directory contains Supabase Edge Functions for the RAG (Retrieval-Augmented Generation) application. These functions handle document vectorization, RAG queries, and thread management with archival capabilities.

## Functions Overview

### 1. `vectorize/` - Document and Chat History Vectorization
Handles the processing and vectorization of uploaded documents and chat history using Langchain.js and OpenAI embeddings.

### 2. `rag-query/` - RAG Query Processing
Performs similarity search on vectorized content and generates AI responses using OpenAI GPT models.

### 3. `delete-thread/` - Thread Deletion with Archival
Handles thread deletion with automatic archival of conversation history before removal.

## API Endpoints

### Vectorization Endpoint
**URL:** `https://your-project.supabase.co/functions/v1/vectorize`
**Method:** POST

#### Document Vectorization
```json
{
  "type": "document",
  "documentId": "uuid-of-document",
  "userId": "user-uuid"
}
```

#### Chat History Vectorization
```json
{
  "type": "chat_history",
  "threadId": "uuid-of-thread",
  "userId": "user-uuid"
}
```

#### Response Format
```json
{
  "success": true,
  "message": "Successfully vectorized document into 15 chunks",
  "vectorCount": 15
}
```

### RAG Query Endpoint
**URL:** `https://your-project.supabase.co/functions/v1/rag-query`
**Method:** POST

#### Request Format
```json
{
  "threadId": "uuid-of-thread",
  "userId": "user-uuid",
  "query": "What are the main points in the uploaded documents?",
  "maxResults": 5,
  "includeChatHistory": true,
  "temperature": 0.7
}
```

#### Response Format
```json
{
  "success": true,
  "response": "Based on the uploaded documents, the main points are...",
  "sources": [
    {
      "content": "Document excerpt...",
      "metadata": {
        "document_title": "Sample Document",
        "chunk_index": 0
      },
      "similarity": 0.85
    }
  ]
}
```

### Thread Deletion Endpoint
**URL:** `https://your-project.supabase.co/functions/v1/delete-thread`
**Method:** POST

#### Request Format
```json
{
  "threadId": "uuid-of-thread",
  "userId": "user-uuid",
  "confirmDeletion": true
}
```

#### Response Format
```json
{
  "success": true,
  "message": "Thread \"Research Project\" successfully deleted and archived",
  "archivedConversations": 25
}
```

## Authentication

All endpoints require authentication via JWT token in the Authorization header:

```
Authorization: Bearer <jwt-token>
```

## Environment Variables

The following environment variables must be set in your Supabase project:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
- `OPENAI_API_KEY`: Your OpenAI API key

## Features

### Document Vectorization
- **Text Splitting**: Uses RecursiveCharacterTextSplitter with optimal settings (1000 chars, 200 overlap)
- **Embedding Generation**: OpenAI text-embedding-ada-002 model
- **Metadata Storage**: Rich metadata including document info, chunk indices, and file details
- **Status Tracking**: Documents progress through processing → completed/failed states

### Chat History Vectorization
- **Intelligent Chunking**: Groups conversations by time proximity (1-hour windows)
- **Context Preservation**: Maintains conversation flow and role information
- **Metadata Enrichment**: Includes date ranges, conversation counts, and role information

### RAG Query Processing
- **Similarity Search**: Vector similarity search using PGVector
- **Context Assembly**: Combines relevant chunks for comprehensive responses
- **Source Attribution**: Returns source information with similarity scores
- **Conversation Logging**: Automatically saves queries and responses

### Thread Archival
- **Complete History**: Archives entire conversation history before deletion
- **Vector Storage**: Stores archived content as searchable vectors
- **Metadata Preservation**: Maintains thread metadata and conversation structure
- **Cascade Deletion**: Removes all associated data in a single transaction

## Usage Examples

### Frontend Integration

#### Document Upload and Vectorization
```typescript
// After uploading document to Supabase Storage
const vectorizeResponse = await fetch('/functions/v1/vectorize', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    type: 'document',
    documentId: uploadedDocument.id,
    userId: user.id
  })
});

const result = await vectorizeResponse.json();
if (result.success) {
  console.log(`Document vectorized into ${result.vectorCount} chunks`);
}
```

#### RAG Query
```typescript
const queryResponse = await fetch('/functions/v1/rag-query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    threadId: currentThread.id,
    userId: user.id,
    query: userQuestion,
    maxResults: 5,
    includeChatHistory: true
  })
});

const result = await queryResponse.json();
if (result.success) {
  displayResponse(result.response, result.sources);
}
```

#### Thread Deletion
```typescript
const deleteResponse = await fetch('/functions/v1/delete-thread', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${userToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    threadId: threadToDelete.id,
    userId: user.id,
    confirmDeletion: true
  })
});

const result = await deleteResponse.json();
if (result.success) {
  console.log(`Thread archived with ${result.archivedConversations} conversations`);
}
```

## Error Handling

All functions return consistent error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error information"
}
```

Common error scenarios:
- **401**: Authentication required or invalid token
- **403**: Unauthorized access to resource
- **404**: Resource not found
- **400**: Invalid request parameters
- **500**: Internal server error

## Performance Considerations

- **Vectorization**: Aim for <5s per small document
- **RAG Queries**: Target <3s response time
- **Batch Processing**: Consider batching multiple documents for efficiency
- **Caching**: Implement client-side caching for frequently accessed content

## Security Features

- **Row Level Security (RLS)**: All database operations respect user scoping
- **JWT Authentication**: Secure token-based authentication
- **User Verification**: All operations verify user ownership of resources
- **Input Validation**: Comprehensive request validation and sanitization

## Monitoring and Logging

- **Supabase Logs**: All function executions are logged
- **Error Tracking**: Detailed error messages for debugging
- **Performance Metrics**: Response times and success rates
- **Usage Analytics**: Track function usage patterns

## Deployment

1. **Deploy Functions**:
   ```bash
   supabase functions deploy vectorize
   supabase functions deploy rag-query
   supabase functions deploy delete-thread
   ```

2. **Set Environment Variables**:
   ```bash
   supabase secrets set SUPABASE_URL=your-project-url
   supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your-service-key
   supabase secrets set OPENAI_API_KEY=your-openai-key
   ```

3. **Run Database Migrations**:
   ```bash
   supabase db push
   ```

## Testing

Test the functions using the Supabase CLI:

```bash
# Test vectorization
supabase functions serve vectorize --env-file .env.local

# Test RAG query
supabase functions serve rag-query --env-file .env.local

# Test thread deletion
supabase functions serve delete-thread --env-file .env.local
```

## Troubleshooting

### Common Issues

1. **Vectorization Fails**: Check document content and OpenAI API key
2. **RAG Query Returns No Results**: Verify documents are vectorized and thread filtering is correct
3. **Authentication Errors**: Ensure JWT token is valid and not expired
4. **Database Errors**: Check RLS policies and user permissions

### Debug Mode

Enable detailed logging by setting the `DEBUG` environment variable:

```bash
supabase secrets set DEBUG=true
```

## Contributing

When adding new features:
1. Follow the existing code structure and patterns
2. Add comprehensive error handling
3. Include proper TypeScript types
4. Update this documentation
5. Add appropriate tests 