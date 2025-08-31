# Thread Deletion Flow Diagram

This diagram shows the complete thread deletion process including confirmation, archival, vector preservation, and cascade deletion for multiple threads per user.

```mermaid
flowchart TD
    %% User Interface
    UI[User Interface<br/>Thread Management] --> DELETE_BTN[Delete Thread Button]
    DELETE_BTN --> CONFIRM_DIALOG{Confirmation Dialog<br/>"Are you sure?"}
    
    %% Confirmation Flow
    CONFIRM_DIALOG -->|Cancel| CANCEL[Cancel Deletion<br/>Return to UI]
    CONFIRM_DIALOG -->|Confirm| DELETE_EF[Edge Function<br/>delete-thread]
    
    %% Validation
    DELETE_EF --> VALIDATE_USER[Validate User Ownership<br/>Check thread belongs to user]
    VALIDATE_USER -->|Invalid| ACCESS_DENIED[Access Denied<br/>Error Response]
    VALIDATE_USER -->|Valid| CHECK_CONFIRMATION[Check confirmDeletion<br/>Must be explicitly true]
    
    %% Confirmation Check
    CHECK_CONFIRMATION -->|False| CONFIRMATION_ERROR[Error: Confirmation Required<br/>confirmDeletion must be true]
    CHECK_CONFIRMATION -->|True| GET_THREAD_DATA[Get Thread Data<br/>threads table]
    
    %% Thread Data Retrieval
    GET_THREAD_DATA --> GET_CONVERSATIONS[Get All Conversations<br/>conversations table]
    GET_CONVERSATIONS --> GET_DOCUMENTS[Get Thread Documents<br/>documents table]
    GET_DOCUMENTS --> GET_VECTORS[Get Document Vectors<br/>vector_chunks table]
    
    %% Archive Creation
    GET_VECTORS --> CREATE_ARCHIVE[Create Thread Archive<br/>Comprehensive Content]
    CREATE_ARCHIVE --> ARCHIVE_CONTENT[Archive Content:<br/>- Thread title & metadata<br/>- All conversations<br/>- Document summaries<br/>- Timestamps & user info]
    
    %% Vector Archive Storage
    ARCHIVE_CONTENT --> VECTORIZE_ARCHIVE[Vectorize Archive Content<br/>OpenAI ada-002]
    VECTORIZE_ARCHIVE --> STORE_ARCHIVE_VECTOR[Store Archive Vector<br/>vector_chunks table<br/>metadata: source_type='thread_archive']
    
    %% Archive Metadata
    STORE_ARCHIVE_VECTOR --> ARCHIVE_METADATA[Archive Metadata:<br/>- archived_from: thread_id<br/>- archived_at: timestamp<br/>- conversation_count<br/>- document_count<br/>- user_id]
    
    %% Cascade Deletion
    ARCHIVE_METADATA --> CASCADE_DELETE[Cascade Deletion<br/>RPC: delete_thread_cascade]
    
    %% Database Cleanup
    CASCADE_DELETE --> DELETE_CONVERSATIONS[Delete Conversations<br/>conversations table]
    DELETE_CONVERSATIONS --> DELETE_DOCUMENTS[Delete Documents<br/>documents table]
    DELETE_DOCUMENTS --> DELETE_DOC_VECTORS[Delete Document Vectors<br/>vector_chunks table]
    DELETE_DOC_VECTORS --> DELETE_THREAD[Delete Thread<br/>threads table]
    
    %% Storage Cleanup
    DELETE_THREAD --> CLEANUP_STORAGE[Cleanup Storage Files<br/>Supabase Storage]
    CLEANUP_STORAGE --> VERIFY_DELETION[Verify Complete Deletion<br/>Check all related data]
    
    %% Success Response
    VERIFY_DELETION --> SUCCESS_RESPONSE[Success Response:<br/>- archivedConversations: count<br/>- archivedVectors: count<br/>- message: "Thread deleted and archived"]
    SUCCESS_RESPONSE --> UI_UPDATE[Update UI<br/>Remove thread from list]
    
    %% Error Handling
    ACCESS_DENIED --> ERROR_RESPONSE[Error Response<br/>Return to UI]
    CONFIRMATION_ERROR --> ERROR_RESPONSE
    ERROR_RESPONSE --> UI_UPDATE
    
    %% Multi-Thread Considerations
    subgraph "Multi-Thread Context"
        USER_THREADS[User's Threads<br/>Multiple active threads]
        THREAD_ISOLATION[Thread Isolation<br/>Each thread independent]
        CROSS_THREAD_ARCHIVE[Cross-Thread Archive<br/>Searchable in future queries]
    end
    
    %% Archive Search Integration
    subgraph "Archive Integration"
        FUTURE_QUERY[Future RAG Query<br/>Include thread archives]
        SEARCH_ARCHIVES[Search Thread Archives<br/>vector_chunks table<br/>source_type='thread_archive']
        ARCHIVE_CONTEXT[Archive Context<br/>Include in RAG response]
    end
    
    %% Database Tables
    subgraph "Database Tables"
        THREADS[(threads<br/>table)]
        CONVERSATIONS[(conversations<br/>table)]
        DOCUMENTS[(documents<br/>table)]
        VECTORS[(vector_chunks<br/>table)]
        USER_PROFILES[(user_profiles<br/>table)]
    end
    
    %% External Services
    subgraph "External Services"
        OPENAI[OpenAI API<br/>ada-002 embeddings]
        SUPABASE[Supabase<br/>Storage & RPC]
    end
    
    %% Edge Functions
    subgraph "Edge Functions"
        DELETE_EF
    end
    
    %% Connect to Database Tables
    GET_THREAD_DATA --> THREADS
    GET_CONVERSATIONS --> CONVERSATIONS
    GET_DOCUMENTS --> DOCUMENTS
    GET_VECTORS --> VECTORS
    STORE_ARCHIVE_VECTOR --> VECTORS
    DELETE_CONVERSATIONS --> CONVERSATIONS
    DELETE_DOCUMENTS --> DOCUMENTS
    DELETE_DOC_VECTORS --> VECTORS
    DELETE_THREAD --> THREADS
    
    %% Connect to External Services
    VECTORIZE_ARCHIVE --> OPENAI
    CLEANUP_STORAGE --> SUPABASE
    CASCADE_DELETE --> SUPABASE
    
    %% Connect Archive Integration
    SEARCH_ARCHIVES --> VECTORS
    FUTURE_QUERY --> SEARCH_ARCHIVES
    
    %% Styling
    classDef userAction fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef database fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef edgeFunction fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef externalService fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef process fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef decision fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef archive fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class UI,DELETE_BTN userAction
    class THREADS,CONVERSATIONS,DOCUMENTS,VECTORS,USER_PROFILES database
    class DELETE_EF edgeFunction
    class OPENAI,SUPABASE externalService
    class VALIDATE_USER,GET_THREAD_DATA,GET_CONVERSATIONS,GET_DOCUMENTS,GET_VECTORS,CREATE_ARCHIVE,VECTORIZE_ARCHIVE,STORE_ARCHIVE_VECTOR,CASCADE_DELETE,DELETE_CONVERSATIONS,DELETE_DOCUMENTS,DELETE_DOC_VECTORS,DELETE_THREAD,CLEANUP_STORAGE,VERIFY_DELETION,SUCCESS_RESPONSE,UI_UPDATE process
    class CONFIRM_DIALOG,CHECK_CONFIRMATION decision
    class ACCESS_DENIED,CONFIRMATION_ERROR,ERROR_RESPONSE error
    class ARCHIVE_CONTENT,ARCHIVE_METADATA,SEARCH_ARCHIVES,ARCHIVE_CONTEXT archive
```

## Process Details

### 1. Confirmation Workflow
1. **User Action**: User clicks "Delete Thread" button
2. **Confirmation Dialog**: Show warning with thread details
3. **User Decision**: User must explicitly confirm deletion
4. **Validation**: Check `confirmDeletion` parameter is `true`

### 2. Pre-Deletion Validation
1. **User Ownership**: Verify thread belongs to authenticated user
2. **Thread Existence**: Check thread exists and is accessible
3. **Permission Check**: Ensure user has delete permissions
4. **Confirmation Check**: Validate `confirmDeletion` is explicitly `true`

### 3. Archive Creation Process
1. **Data Collection**: Gather all thread-related data:
   - Thread metadata (title, created_at, updated_at)
   - All conversations (user and assistant messages)
   - Document summaries and metadata
   - User information and timestamps

2. **Archive Content**: Create comprehensive archive:
   ```
   Thread Archive: [Thread Title]
   Created: [timestamp]
   User: [user_email]
   
   Conversations:
   - [timestamp] User: [message]
   - [timestamp] Assistant: [response]
   ...
   
   Documents:
   - [document_title] ([file_type])
   - [document_title] ([file_type])
   ...
   
   Summary: [conversation_count] conversations, [document_count] documents
   ```

3. **Vectorization**: Generate embeddings for archive content
4. **Storage**: Store archive vector with metadata:
   - `source_type: 'thread_archive'`
   - `archived_from: thread_id`
   - `archived_at: timestamp`
   - `conversation_count: number`
   - `document_count: number`

### 4. Cascade Deletion Process
1. **RPC Call**: Execute `delete_thread_cascade` function
2. **Conversations**: Delete all conversations in thread
3. **Documents**: Delete all documents in thread
4. **Document Vectors**: Delete all vector chunks for documents
5. **Thread**: Delete the thread record
6. **Storage Files**: Clean up uploaded files from storage

### 5. Database Table Interactions

#### `threads` Table
- **Read**: Get thread data and metadata
- **Delete**: Remove thread record (cascade deletes related data)

#### `conversations` Table
- **Read**: Get all conversations for archiving
- **Delete**: Remove all conversations in thread

#### `documents` Table
- **Read**: Get document metadata for archiving
- **Delete**: Remove all documents in thread

#### `vector_chunks` Table
- **Read**: Get document vectors for archiving
- **Create**: Store archive vector with metadata
- **Delete**: Remove document vectors (keep archive vector)

### 6. Archive Integration with RAG

#### Future Query Inclusion
- Archive vectors are included in RAG searches
- Search across `source_type='thread_archive'` vectors
- Provide context from deleted threads in responses

#### Archive Search Example
```sql
-- Search including thread archives
SELECT * FROM vector_chunks 
WHERE user_id = $1 
AND (
  metadata->>'source_type' = 'document' 
  OR metadata->>'source_type' = 'thread_archive'
)
ORDER BY embedding <=> $2
LIMIT 10;
```

### 7. Multi-Thread Considerations

#### Thread Isolation
- Each thread is completely independent
- Deletion of one thread doesn't affect others
- User can have multiple active threads simultaneously

#### Cross-Thread Archive Search
- Archive vectors are searchable across all user's threads
- Future queries can include context from archived threads
- Maintains conversation history for reference

### 8. Error Handling

#### Validation Errors
- **Access Denied**: Thread doesn't belong to user
- **Confirmation Required**: `confirmDeletion` not set to `true`
- **Thread Not Found**: Thread doesn't exist

#### Processing Errors
- **Archive Creation Failed**: Vectorization or storage error
- **Cascade Deletion Failed**: Database constraint violation
- **Storage Cleanup Failed**: File deletion error

### 9. Security Features

#### User Scoping
- All operations scoped to authenticated user
- RLS policies prevent cross-user access
- Service role used for cascade deletion

#### Confirmation Requirements
- Explicit confirmation required (`confirmDeletion: true`)
- Cannot be bypassed with truthy values
- Prevents accidental deletions

#### Data Preservation
- Complete archive created before deletion
- Archive searchable in future queries
- Maintains conversation history for reference

### 10. Performance Considerations

#### Batch Operations
- Archive creation in single operation
- Cascade deletion via database RPC
- Storage cleanup in background

#### Vector Optimization
- Archive vector stored with optimized metadata
- Efficient search across archive vectors
- Minimal storage overhead for archives 