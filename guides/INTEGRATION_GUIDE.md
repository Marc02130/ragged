# RAG Application Integration Guide

## Overview

This guide explains how the RAG (Retrieval-Augmented Generation) application integrates React frontend with Supabase Edge Functions to provide seamless document upload, vectorization, chat queries, and thread management.

## Architecture

### Frontend (React + TypeScript + Vite)
- **Authentication**: Supabase Auth with JWT tokens
- **State Management**: React hooks (useState, useEffect)
- **Styling**: Tailwind CSS
- **Components**: Modular React components for each feature

### Backend (Supabase Edge Functions)
- **Vectorization**: Langchain.js for document processing and embeddings
- **RAG Queries**: OpenAI API for context-aware responses
- **Thread Management**: Complete CRUD operations with archival
- **Database**: PostgreSQL with pgvector extension

### Database Schema
- **users**: Supabase Auth users
- **threads**: Conversation threads per user
- **documents**: Uploaded documents with metadata
- **vector_chunks**: Document embeddings for similarity search
- **conversations**: Chat messages with vectorization status

## Integration Flow

### 1. User Authentication
```typescript
// src/lib/supabase.ts
export const auth = {
  signIn: async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { data, error };
  },
  // ... other auth methods
};
```

### 2. Thread Management
```typescript
// Create new thread
const { data, error } = await threads.create("My New Thread");

// List user threads
const { data, error } = await threads.list();

// Delete thread with archival
const { data, error } = await threads.delete(threadId);
```

### 3. Document Upload & Vectorization
```typescript
// Upload documents to thread
const { data, error } = await documents.upload(files, threadId);

// Edge Function: vectorize/index.ts
// - Processes uploaded documents
// - Splits into chunks using Langchain
// - Generates embeddings with OpenAI
// - Stores in vector_chunks table
```

### 4. RAG Chat Queries
```typescript
// Send message to RAG system
const { data, error } = await chat.sendMessage(threadId, message);

// Edge Function: rag-query/index.ts
// - Generates query embedding
// - Performs similarity search across documents and chat history
// - Retrieves relevant context
// - Generates response using OpenAI
// - Saves conversation to database
```

### 5. Thread Deletion with Archival
```typescript
// Delete thread with confirmation
const { data, error } = await threads.delete(threadId);

// Edge Function: delete-thread/index.ts
// - Archives complete conversation history
// - Vectorizes archived content
// - Deletes live thread data
// - Maintains searchable archive
```

## Key Features

### Multi-Thread Support
- Users can create multiple conversation threads
- Each thread has its own document collection
- Cross-thread search capabilities
- Thread-specific vectorization

### Document Processing
- Support for PDF, DOCX, TXT, RTF files
- Automatic chunking and vectorization
- Progress tracking during upload
- Error handling and retry mechanisms

### Intelligent Chat
- Context-aware responses using RAG
- Chat history vectorization for recall
- Source attribution and similarity scores
- Fallback responses when no context found

### Thread Archival
- Complete conversation preservation
- Vectorized archive for future reference
- Confirmation dialogs for deletion
- Restore functionality for archived threads

## Environment Configuration

### Required Environment Variables
```bash
# Supabase
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Application
NODE_ENV=development
```

### Database Setup
1. Run migrations in order:
   ```sql
   -- 00000_initial_schema.sql
   -- 00001_thread_deletion_function.sql
   -- 00002_vector_chunks_optimization.sql
   -- 00003_fix_schema_consistency.sql
   ```

2. Enable required extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "vector";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   ```

### Edge Functions Deployment
```bash
# Deploy all Edge Functions
supabase functions deploy vectorize
supabase functions deploy rag-query
supabase functions deploy delete-thread

# Set environment variables
supabase secrets set OPENAI_API_KEY=your-key
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your-key
```

## Component Integration

### App.tsx - Main Application
- Manages authentication state
- Coordinates between components
- Handles thread selection and switching
- Provides error boundaries and loading states

### ThreadList.tsx - Thread Management
- Displays user's threads
- Handles thread creation, archiving, deletion
- Shows archived threads with restore option
- Confirmation dialogs for destructive actions

### DocumentUpload.tsx - File Processing
- Drag-and-drop file upload
- File validation and progress tracking
- Integration with vectorization Edge Function
- Error handling and user feedback

### ChatInterface.tsx - RAG Conversations
- Real-time chat interface
- RAG query integration
- Source attribution display
- Message history management

## Security Features

### Row Level Security (RLS)
- All tables have RLS enabled
- User-scoped data access
- Thread-specific document isolation
- Secure vector chunk access

### Authentication
- JWT-based authentication
- Edge Function authorization
- User ownership verification
- Secure API endpoints

### Data Privacy
- User data isolation
- Secure file storage
- Encrypted API communications
- Audit trail for sensitive operations

## Performance Optimizations

### Vector Search
- Efficient similarity search using pgvector
- Batch processing for large documents
- Rate limiting for API calls
- Caching for frequent queries

### Database Optimization
- Proper indexing on search fields
- Efficient query patterns
- Connection pooling
- Transaction management

### Frontend Performance
- Lazy loading of components
- Optimistic UI updates
- Efficient state management
- Minimal re-renders

## Error Handling

### Frontend Error Handling
- Error boundaries for component failures
- Toast notifications for user feedback
- Graceful degradation for API failures
- Retry mechanisms for transient errors

### Backend Error Handling
- Comprehensive error logging
- Structured error responses
- Transaction rollback on failures
- Rate limiting and timeout handling

## Testing Strategy

### Unit Tests
- Component functionality
- Utility functions
- API integration
- Error scenarios

### Integration Tests
- End-to-end workflows
- Database operations
- Edge Function testing
- Authentication flows

### Performance Tests
- Vector search performance
- Document processing speed
- Concurrent user handling
- Memory usage optimization

## Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Edge Functions deployed
- [ ] Storage buckets created
- [ ] RLS policies verified

### Post-Deployment
- [ ] Authentication flow tested
- [ ] Document upload verified
- [ ] Chat functionality working
- [ ] Thread management operational
- [ ] Error handling validated

## Troubleshooting

### Common Issues
1. **Vectorization failures**: Check OpenAI API key and quotas
2. **Authentication errors**: Verify JWT configuration
3. **Database connection issues**: Check connection strings and RLS policies
4. **File upload problems**: Verify storage bucket permissions

### Debug Tools
- Supabase Dashboard for database inspection
- Edge Function logs for backend debugging
- Browser DevTools for frontend issues
- Network tab for API call analysis

## Future Enhancements

### Planned Features
- Real-time collaboration
- Advanced document types
- Custom embedding models
- Analytics dashboard
- Export functionality

### Scalability Considerations
- Horizontal scaling for Edge Functions
- Database sharding strategies
- CDN integration for file storage
- Caching layer implementation

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Edge Function logs
3. Verify environment configuration
4. Test with minimal setup
5. Consult Supabase and OpenAI documentation

This integration provides a complete RAG application with robust document processing, intelligent chat capabilities, and comprehensive thread management. 