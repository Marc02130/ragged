# Upload-to-Query Data Flow Diagram

This diagram shows the complete data flow from document upload through processing to RAG query execution, including all database table interactions and Edge Function calls.

```mermaid
flowchart TD
    %% User Interface Components
    UI[User Interface<br/>React Frontend] --> UPLOAD[Document Upload<br/>Drag & Drop]
    UI --> QUERY[Chat Query<br/>User Input]
    
    %% Upload Flow
    UPLOAD --> VALIDATE{Validate File<br/>Size & Type}
    VALIDATE -->|Valid| CREATE_DOC[Create Document Record<br/>documents table]
    VALIDATE -->|Invalid| ERROR[Error: Invalid File]
    
    CREATE_DOC --> UPLOAD_FILE[Upload to Storage<br/>Supabase Storage]
    UPLOAD_FILE --> EXTRACT[Extract Text Content<br/>PDF/DOCX/TXT]
    
    %% Vectorization Flow
    EXTRACT --> VECTORIZE_EF[Edge Function<br/>vectorize]
    VECTORIZE_EF --> SPLIT[Text Splitting<br/>Langchain.js]
    SPLIT --> EMBED[Generate Embeddings<br/>OpenAI ada-002]
    EMBED --> STORE_VECTORS[Store Vector Chunks<br/>vector_chunks table]
    STORE_VECTORS --> UPDATE_STATUS[Update Document Status<br/>documents table]
    
    %% Query Flow
    QUERY --> QUERY_EF[Edge Function<br/>rag-query]
    QUERY_EF --> GET_EMBEDDING[Generate Query Embedding<br/>OpenAI ada-002]
    GET_EMBEDDING --> VECTOR_SEARCH[Vector Similarity Search<br/>vector_chunks table]
    
    %% Context Building
    VECTOR_SEARCH --> GET_CONTEXT[Retrieve Context<br/>documents table]
    GET_CONTEXT --> GET_HISTORY{Include Chat History?}
    GET_HISTORY -->|Yes| GET_CONVERSATIONS[Get Conversations<br/>conversations table]
    GET_HISTORY -->|No| BUILD_PROMPT[Build RAG Prompt]
    GET_CONVERSATIONS --> BUILD_PROMPT
    
    %% Cross-Thread Search
    BUILD_PROMPT --> CROSS_THREAD{Cross-Thread Search?}
    CROSS_THREAD -->|Yes| SEARCH_THREADS[Search Multiple Threads<br/>threads table]
    CROSS_THREAD -->|No| GENERATE_RESPONSE[Generate AI Response<br/>OpenAI GPT-4]
    SEARCH_THREADS --> GENERATE_RESPONSE
    
    %% Response Handling
    GENERATE_RESPONSE --> SAVE_CONVERSATION[Save Conversation<br/>conversations table]
    SAVE_CONVERSATION --> UPDATE_THREAD[Update Thread Activity<br/>threads table]
    UPDATE_THREAD --> RETURN_RESPONSE[Return Response<br/>Sources & Context]
    RETURN_RESPONSE --> UI
    
    %% Error Handling
    ERROR --> UI
    VECTORIZE_EF -->|Error| ERROR_VECTOR[Vectorization Error]
    QUERY_EF -->|Error| ERROR_QUERY[Query Error]
    ERROR_VECTOR --> UI
    ERROR_QUERY --> UI
    
    %% Database Tables
    subgraph "Database Tables"
        DOCS[(documents<br/>table)]
        VECTORS[(vector_chunks<br/>table)]
        THREADS[(threads<br/>table)]
        CONVERSATIONS[(conversations<br/>table)]
        USER_PROFILES[(user_profiles<br/>table)]
    end
    
    %% External Services
    subgraph "External Services"
        OPENAI[OpenAI API<br/>GPT-4 & ada-002]
        SUPABASE[Supabase<br/>Auth & Storage]
    end
    
    %% Edge Functions
    subgraph "Edge Functions"
        VECTORIZE_EF
        QUERY_EF
    end
    
    %% Connect to Database Tables
    CREATE_DOC --> DOCS
    STORE_VECTORS --> VECTORS
    UPDATE_STATUS --> DOCS
    VECTOR_SEARCH --> VECTORS
    GET_CONTEXT --> DOCS
    GET_CONVERSATIONS --> CONVERSATIONS
    SEARCH_THREADS --> THREADS
    SAVE_CONVERSATION --> CONVERSATIONS
    UPDATE_THREAD --> THREADS
    
    %% Connect to External Services
    EMBED --> OPENAI
    GET_EMBEDDING --> OPENAI
    GENERATE_RESPONSE --> OPENAI
    UPLOAD_FILE --> SUPABASE
    
    %% Styling
    classDef userAction fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef database fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef edgeFunction fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef externalService fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef process fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef decision fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px
    
    class UI,UPLOAD,QUERY userAction
    class DOCS,VECTORS,THREADS,CONVERSATIONS,USER_PROFILES database
    class VECTORIZE_EF,QUERY_EF edgeFunction
    class OPENAI,SUPABASE externalService
    class CREATE_DOC,UPLOAD_FILE,EXTRACT,SPLIT,EMBED,STORE_VECTORS,UPDATE_STATUS,GET_EMBEDDING,VECTOR_SEARCH,GET_CONTEXT,GET_CONVERSATIONS,BUILD_PROMPT,SEARCH_THREADS,GENERATE_RESPONSE,SAVE_CONVERSATION,UPDATE_THREAD,RETURN_RESPONSE process
    class VALIDATE,GET_HISTORY,CROSS_THREAD decision
    class ERROR,ERROR_VECTOR,ERROR_QUERY error
```

## Process Details

### 1. Document Upload Flow
1. **File Validation**: Check file size (max 10MB) and type (PDF, DOCX, TXT, RTF)
2. **Database Record**: Create entry in `documents` table with status 'processing'
3. **Storage Upload**: Upload file to Supabase Storage with user-scoped path
4. **Text Extraction**: Extract text content from uploaded file
5. **Vectorization**: Process through Edge Function with Langchain.js
6. **Chunking**: Split text into 1000-token chunks with 200-token overlap
7. **Embedding**: Generate 1536-dimensional vectors using OpenAI ada-002
8. **Storage**: Store vectors in `vector_chunks` table with metadata
9. **Status Update**: Update document status to 'completed'

### 2. RAG Query Flow
1. **Query Input**: User submits question through chat interface
2. **Query Embedding**: Generate embedding for user query
3. **Vector Search**: Find similar chunks using cosine similarity
4. **Context Retrieval**: Get source documents and metadata
5. **Chat History**: Optionally include recent conversations
6. **Cross-Thread Search**: Optionally search across multiple threads
7. **Prompt Building**: Construct RAG prompt with context and history
8. **AI Generation**: Generate response using OpenAI GPT-4
9. **Response Storage**: Save conversation in `conversations` table
10. **Thread Update**: Update thread's last activity timestamp

### 3. Database Table Interactions

#### `documents` Table
- **Create**: New document record during upload
- **Update**: Status changes (processing → completed)
- **Read**: Retrieve document metadata for context

#### `vector_chunks` Table
- **Create**: Store document embeddings with metadata
- **Read**: Vector similarity search for RAG queries
- **Update**: Metadata updates (rare)

#### `threads` Table
- **Read**: Get user's threads for cross-thread search
- **Update**: Update last_activity_at timestamp

#### `conversations` Table
- **Create**: Save user queries and AI responses
- **Read**: Retrieve chat history for context

### 4. Edge Function Details

#### `vectorize` Function
- **Input**: Document ID, user ID, content, file metadata
- **Process**: Text splitting, embedding generation, batch storage
- **Output**: Vector count, processing status, error handling

#### `rag-query` Function
- **Input**: Thread ID, user ID, query, search options
- **Process**: Vector search, context building, AI generation
- **Output**: AI response, sources, performance metrics

### 5. Security & Scoping
- **User Isolation**: All operations scoped to authenticated user
- **RLS Policies**: Database access controlled by Row Level Security
- **File Validation**: Comprehensive file type and size validation
- **Error Handling**: Graceful error handling with user feedback

### 6. Performance Considerations
- **Batch Processing**: Vector storage in batches for efficiency
- **Caching**: Query results cached for repeated requests
- **Indexing**: Optimized vector indexes for similarity search
- **Rate Limiting**: API rate limits to prevent abuse 