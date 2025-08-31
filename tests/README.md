# RAG App Test Suite

This comprehensive test suite covers all aspects of the RAG application as specified in the PRD, including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── unit/                    # Unit tests for Edge Functions and Langchain
│   ├── setup.ts            # Unit test configuration and mocks
│   └── vectorization.test.ts # Langchain vectorization tests
├── integration/            # Integration tests for Supabase operations
│   ├── setup.ts            # Integration test configuration
│   └── supabase-storage.test.ts # Database operations tests
├── e2e/                    # End-to-end tests for complete workflows
│   ├── setup.ts            # E2E test configuration
│   ├── chat-queries.test.ts # Chat query and RAG workflow tests
│   └── thread-deletion.test.ts # Thread deletion workflow tests
└── README.md               # This file
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)
**Focus**: Langchain vectorization in Edge Functions (per thread)

**Coverage**:
- Document vectorization with proper chunking
- Large document handling with chunk limits
- Chat history vectorization with conversation grouping
- Batch processing with rate limiting
- Error handling for embedding generation
- Utility functions (cosine similarity, chat chunk creation)

**Key Features Tested**:
- RecursiveCharacterTextSplitter configuration
- OpenAI embeddings generation
- Vector chunk metadata creation
- Batch insertion with error handling
- User preference integration

### 2. Integration Tests (`tests/integration/`)
**Focus**: Supabase storage/retrieval (documents/threads tables)

**Coverage**:
- Document table operations (CRUD)
- Thread table operations (CRUD)
- Vector chunks table operations
- Conversations table operations
- User preferences operations
- RLS (Row Level Security) compliance
- Database transaction handling

**Key Features Tested**:
- Document creation and status updates
- Thread management with proper ordering
- Vector chunk insertion and similarity search
- Conversation history management
- User preference retrieval with defaults
- Error handling for database operations

### 3. End-to-End Tests (`tests/e2e/`)
**Focus**: Complete workflows including chat queries and thread management

**Coverage**:
- Complete RAG query flow with OpenAI
- Cross-thread search functionality
- Chat history vectorization integration
- Multiple threads per user management
- Thread deletion with archival
- Confirmation workflows

**Key Features Tested**:
- RAG query with document retrieval
- Fallback response generation
- Cross-thread similarity search
- Chat history inclusion in queries
- Thread isolation and data privacy
- Complete deletion workflow with confirmation

## Test Configuration

### Vitest Configurations

1. **Unit Tests** (`vitest.unit.config.ts`)
   - Environment: Node.js
   - Focus: Edge Functions and Langchain
   - Coverage: Vectorization logic

2. **Integration Tests** (`vitest.integration.config.ts`)
   - Environment: Node.js
   - Focus: Database operations
   - Coverage: Supabase interactions

3. **E2E Tests** (`vitest.e2e.config.ts`)
   - Environment: Happy-DOM
   - Focus: Complete user workflows
   - Coverage: Full application flows

## Running Tests

### Install Dependencies
```bash
npm install
```

### Run All Tests
```bash
npm test
```

### Run Specific Test Categories
```bash
# Unit tests only
npm run test:unit

# Integration tests only
npm run test:integration

# E2E tests only
npm run test:e2e
```

### Run with Coverage
```bash
npm run test:coverage
```

### Run in Watch Mode
```bash
npm run test:watch
```

## Test Data and Mocking

### Mock Strategy
- **Supabase Client**: Mocked with comprehensive query chain support
- **OpenAI APIs**: Mocked for embeddings and LLM responses
- **Langchain**: Mocked for text splitting and document processing
- **React Components**: Mocked for UI testing

### Test Data Examples
```typescript
// Sample document for testing
const mockDocument = {
  id: 'doc-123',
  thread_id: 'thread-456',
  user_id: 'user-789',
  title: 'Test Document',
  content: 'This is test content for vectorization.',
  status: 'pending'
}

// Sample conversation for testing
const mockConversation = {
  id: 'conv-1',
  thread_id: 'thread-123',
  user_id: 'user-456',
  role: 'user',
  content: 'What is the main topic?',
  created_at: '2024-01-01T10:00:00Z'
}
```

## Test Scenarios Covered

### Vectorization Tests
1. **Document Processing**
   - Small document vectorization
   - Large document with chunk limits
   - Error handling for missing content
   - Embedding generation failures

2. **Chat History Processing**
   - Conversation grouping by time
   - Meaningful chunk creation
   - Metadata preservation
   - Empty conversation handling

3. **Batch Processing**
   - Rate limiting between batches
   - Error handling in batch operations
   - Progress tracking
   - Memory optimization

### Database Integration Tests
1. **Document Management**
   - Create, read, update operations
   - Status tracking (pending → processing → completed)
   - User-scoped access control
   - Error handling

2. **Thread Management**
   - Thread creation and listing
   - Activity timestamp updates
   - Status changes (active → archived)
   - Cascade deletion

3. **Vector Operations**
   - Similarity search with filtering
   - Batch insertion with metadata
   - Cross-thread search capabilities
   - Performance optimization

### E2E Workflow Tests
1. **RAG Query Flow**
   - Complete query processing
   - Document retrieval and ranking
   - Response generation with sources
   - Fallback handling

2. **Cross-Thread Search**
   - Multiple thread discovery
   - Relevance scoring across threads
   - Source attribution
   - Performance metrics

3. **Thread Deletion**
   - Confirmation workflow
   - Archive creation
   - Vector storage
   - Cascade deletion
   - Error recovery

## Performance Testing

### Vectorization Performance
- Large document processing (>10,000 characters)
- Batch processing with rate limiting
- Memory usage optimization
- Processing time tracking

### Database Performance
- Batch insertion operations
- Similarity search optimization
- Concurrent user handling
- Query performance monitoring

### E2E Performance
- Complete RAG query response times
- Cross-thread search performance
- Thread deletion workflow timing
- User interaction responsiveness

## Error Handling Tests

### Vectorization Errors
- OpenAI API rate limits
- Invalid document content
- Embedding generation failures
- Database insertion errors

### Database Errors
- Connection failures
- RLS policy violations
- Transaction rollbacks
- Constraint violations

### User Interface Errors
- Invalid user input
- Network failures
- Authentication errors
- Permission denied scenarios

## Security and Privacy Tests

### Data Isolation
- User-scoped data access
- Thread isolation
- Cross-user data protection
- RLS policy enforcement

### Authentication
- JWT token validation
- User preference access
- Resource ownership verification
- Unauthorized access prevention

### Data Privacy
- Sensitive data handling
- Archive content protection
- Deletion confirmation
- Audit trail maintenance

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:unit
      - run: npm run test:integration
      - run: npm run test:e2e
      - run: npm run test:coverage
```

### Coverage Requirements
- Unit tests: >90% coverage
- Integration tests: >85% coverage
- E2E tests: >80% coverage
- Overall: >85% coverage

## Best Practices

### Test Organization
- Group related tests in describe blocks
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Keep tests independent and isolated

### Mock Management
- Reset mocks between tests
- Use realistic mock data
- Verify mock interactions
- Test error scenarios

### Performance Considerations
- Use appropriate timeouts
- Mock external API calls
- Optimize database queries
- Monitor memory usage

### Maintenance
- Update tests when APIs change
- Review test coverage regularly
- Refactor common test utilities
- Document test scenarios

## Troubleshooting

### Common Issues
1. **Mock not working**: Ensure mocks are properly reset between tests
2. **Async test failures**: Use proper async/await patterns
3. **Database connection**: Verify Supabase configuration
4. **Memory leaks**: Check for proper cleanup in tests

### Debug Mode
```bash
# Run tests with debug output
DEBUG=* npm run test

# Run specific test with verbose output
npm run test -- --verbose
```

## Contributing

### Adding New Tests
1. Follow existing test patterns
2. Add appropriate mocks
3. Include error scenarios
4. Update documentation
5. Ensure coverage requirements

### Test Review Process
1. Code review for test logic
2. Coverage analysis
3. Performance impact assessment
4. Documentation updates
5. Integration testing

This test suite ensures the RAG application meets all PRD requirements and maintains high quality standards across all components. 