# Database Schema Diagram

This diagram shows the complete database schema for the RAGged application, including all tables, relationships, indexes, and Row Level Security (RLS) policies.

```mermaid
erDiagram
    %% User Authentication
    auth_users {
        UUID id PK
        string email
        timestamp created_at
        timestamp updated_at
        jsonb raw_user_meta_data
    }
    
    %% User Profiles
    user_profiles {
        UUID id PK
        UUID user_id FK
        string full_name
        string avatar_url
        timestamp created_at
        timestamp updated_at
    }
    
    %% Threads
    threads {
        UUID id PK
        UUID user_id FK
        string title
        string status
        timestamp last_activity_at
        timestamp created_at
        timestamp updated_at
    }
    
    %% Documents
    documents {
        UUID id PK
        UUID user_id FK
        UUID thread_id FK
        string title
        string file_name
        integer file_size
        string file_type
        text content
        string status
        timestamp created_at
        timestamp updated_at
    }
    
    %% Vector Chunks
    vector_chunks {
        UUID id PK
        UUID document_id FK
        UUID user_id FK
        text content
        vector embedding
        jsonb metadata
        integer chunk_index
        timestamp created_at
    }
    
    %% Conversations
    conversations {
        UUID id PK
        UUID thread_id FK
        UUID user_id FK
        string role
        text content
        jsonb metadata
        timestamp created_at
    }
    
    %% Relationships
    auth_users ||--o{ user_profiles : "has profile"
    auth_users ||--o{ threads : "owns threads"
    auth_users ||--o{ documents : "owns documents"
    auth_users ||--o{ vector_chunks : "owns vectors"
    auth_users ||--o{ conversations : "owns conversations"
    
    threads ||--o{ documents : "contains documents"
    threads ||--o{ conversations : "contains conversations"
    
    documents ||--o{ vector_chunks : "has vectors"
    
    %% RLS Policies
    subgraph "Row Level Security (RLS) Policies"
        RLS_USER_PROFILES["user_profiles RLS:
        - SELECT: auth.uid() = user_id
        - INSERT: auth.uid() = user_id
        - UPDATE: auth.uid() = user_id"]
        
        RLS_THREADS["threads RLS:
        - SELECT: auth.uid() = user_id
        - INSERT: auth.uid() = user_id
        - UPDATE: auth.uid() = user_id
        - DELETE: auth.uid() = user_id"]
        
        RLS_DOCUMENTS["documents RLS:
        - SELECT: auth.uid() = user_id
        - INSERT: auth.uid() = user_id
        - UPDATE: auth.uid() = user_id
        - DELETE: auth.uid() = user_id"]
        
        RLS_VECTOR_CHUNKS["vector_chunks RLS:
        - SELECT: auth.uid() = user_id
        - INSERT: auth.uid() = user_id
        - UPDATE: auth.uid() = user_id
        - DELETE: auth.uid() = user_id"]
        
        RLS_CONVERSATIONS["conversations RLS:
        - SELECT: auth.uid() = user_id AND thread_id IN (SELECT id FROM threads WHERE user_id = auth.uid())
        - INSERT: auth.uid() = user_id AND thread_id IN (SELECT id FROM threads WHERE user_id = auth.uid())
        - UPDATE: auth.uid() = user_id AND thread_id IN (SELECT id FROM threads WHERE user_id = auth.uid())
        - DELETE: auth.uid() = user_id AND thread_id IN (SELECT id FROM threads WHERE user_id = auth.uid())"]
    end
    
    %% Indexes
    subgraph "Database Indexes"
        IDX_THREADS_USER["threads(user_id)"]
        IDX_THREADS_STATUS["threads(status)"]
        IDX_DOCUMENTS_USER["documents(user_id)"]
        IDX_DOCUMENTS_THREAD["documents(thread_id)"]
        IDX_DOCUMENTS_STATUS["documents(status)"]
        IDX_VECTORS_DOCUMENT["vector_chunks(document_id)"]
        IDX_VECTORS_USER["vector_chunks(user_id)"]
        IDX_VECTORS_EMBEDDING["vector_chunks USING ivfflat(embedding)"]
        IDX_CONVERSATIONS_THREAD["conversations(thread_id)"]
        IDX_CONVERSATIONS_USER["conversations(user_id)"]
    end
    
    %% Functions
    subgraph "Database Functions"
        FUNC_MATCH_DOCS["match_documents(
            query_embedding VECTOR(1536),
            match_threshold FLOAT,
            match_count INT,
            p_user_id UUID,
            p_thread_id UUID
        )"]
        
        FUNC_MATCH_CROSS["match_documents_cross_thread(
            query_embedding VECTOR(1536),
            match_threshold FLOAT,
            match_count INT,
            p_user_id UUID,
            p_thread_ids UUID[]
        )"]
        
        FUNC_DELETE_CASCADE["delete_thread_cascade(
            p_thread_id UUID,
            p_user_id UUID
        )"]
        
        FUNC_UPDATE_TIMESTAMP["update_updated_at_column()"]
    end
    
    %% Triggers
    subgraph "Database Triggers"
        TRIGGER_USER_PROFILES["user_profiles_updated_at"]
        TRIGGER_DOCUMENTS["documents_updated_at"]
        TRIGGER_THREADS["threads_updated_at"]
        TRIGGER_NEW_USER["on_auth_user_created"]
    end
    
    %% Connect RLS to tables
    user_profiles ||--|| RLS_USER_PROFILES : "enforces"
    threads ||--|| RLS_THREADS : "enforces"
    documents ||--|| RLS_DOCUMENTS : "enforces"
    vector_chunks ||--|| RLS_VECTOR_CHUNKS : "enforces"
    conversations ||--|| RLS_CONVERSATIONS : "enforces"
    
    %% Connect indexes to tables
    threads ||--|| IDX_THREADS_USER : "indexed"
    threads ||--|| IDX_THREADS_STATUS : "indexed"
    documents ||--|| IDX_DOCUMENTS_USER : "indexed"
    documents ||--|| IDX_DOCUMENTS_THREAD : "indexed"
    documents ||--|| IDX_DOCUMENTS_STATUS : "indexed"
    vector_chunks ||--|| IDX_VECTORS_DOCUMENT : "indexed"
    vector_chunks ||--|| IDX_VECTORS_USER : "indexed"
    vector_chunks ||--|| IDX_VECTORS_EMBEDDING : "indexed"
    conversations ||--|| IDX_CONVERSATIONS_THREAD : "indexed"
    conversations ||--|| IDX_CONVERSATIONS_USER : "indexed"
    
    %% Connect functions to tables
    vector_chunks ||--|| FUNC_MATCH_DOCS : "queries"
    vector_chunks ||--|| FUNC_MATCH_CROSS : "queries"
    threads ||--|| FUNC_DELETE_CASCADE : "deletes"
    
    %% Connect triggers to tables
    user_profiles ||--|| TRIGGER_USER_PROFILES : "triggers"
    documents ||--|| TRIGGER_DOCUMENTS : "triggers"
    threads ||--|| TRIGGER_THREADS : "triggers"
    auth_users ||--|| TRIGGER_NEW_USER : "triggers"
```

## Schema Details

### 1. Core Tables

#### `auth_users` (Supabase Auth)
```sql
-- Managed by Supabase Auth
-- Contains user authentication data
```

#### `user_profiles`
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `threads`
```sql
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `documents`
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    content TEXT,
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `vector_chunks`
```sql
CREATE TABLE vector_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- OpenAI ada-002 dimension
    metadata JSONB DEFAULT '{}',
    chunk_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### `conversations`
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. Row Level Security (RLS)

#### Enable RLS on All Tables
```sql
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
```

#### User Profiles RLS
```sql
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);
```

#### Threads RLS
```sql
CREATE POLICY "Users can view own threads" ON threads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own threads" ON threads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own threads" ON threads
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own threads" ON threads
    FOR DELETE USING (auth.uid() = user_id);
```

#### Documents RLS
```sql
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents" ON documents
    FOR DELETE USING (auth.uid() = user_id);
```

#### Vector Chunks RLS
```sql
CREATE POLICY "Users can view own vector chunks" ON vector_chunks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own vector chunks" ON vector_chunks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own vector chunks" ON vector_chunks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own vector chunks" ON vector_chunks
    FOR DELETE USING (auth.uid() = user_id);
```

#### Conversations RLS
```sql
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own conversations" ON conversations
    FOR UPDATE USING (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own conversations" ON conversations
    FOR DELETE USING (
        auth.uid() = user_id AND
        thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        )
    );
```

### 3. Database Indexes

#### Performance Indexes
```sql
-- Thread indexes
CREATE INDEX idx_threads_user_id ON threads(user_id);
CREATE INDEX idx_threads_status ON threads(status);

-- Document indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_thread_id ON documents(thread_id);
CREATE INDEX idx_documents_status ON documents(status);

-- Vector chunk indexes
CREATE INDEX idx_vector_chunks_document_id ON vector_chunks(document_id);
CREATE INDEX idx_vector_chunks_user_id ON vector_chunks(user_id);
CREATE INDEX idx_vector_chunks_embedding ON vector_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Conversation indexes
CREATE INDEX idx_conversations_thread_id ON conversations(thread_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
```

### 4. Database Functions

#### Vector Search Functions
```sql
-- Basic vector similarity search
CREATE OR REPLACE FUNCTION match_documents(
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

-- Cross-thread vector search
CREATE OR REPLACE FUNCTION match_documents_cross_thread(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.8,
    match_count INT DEFAULT 10,
    p_user_id UUID,
    p_thread_ids UUID[] DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    thread_id UUID
)
LANGUAGE plpgsql
AS $$
BEGIN
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

#### Cascade Deletion Function
```sql
-- Thread cascade deletion
CREATE OR REPLACE FUNCTION delete_thread_cascade(
    p_thread_id UUID,
    p_user_id UUID
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Delete conversations
    DELETE FROM conversations 
    WHERE thread_id = p_thread_id AND user_id = p_user_id;
    
    -- Delete documents (cascade deletes vector chunks)
    DELETE FROM documents 
    WHERE thread_id = p_thread_id AND user_id = p_user_id;
    
    -- Delete thread
    DELETE FROM threads 
    WHERE id = p_thread_id AND user_id = p_user_id;
END;
$$;
```

### 5. Database Triggers

#### Timestamp Update Trigger
```sql
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_threads_updated_at
    BEFORE UPDATE ON threads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### User Profile Creation Trigger
```sql
-- Function to automatically create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (user_id, full_name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
```

### 6. Extensions

#### Required Extensions
```sql
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
```

### 7. Data Relationships

#### One-to-Many Relationships
- **User → Threads**: One user can have multiple threads
- **User → Documents**: One user can have multiple documents
- **User → Conversations**: One user can have multiple conversations
- **Thread → Documents**: One thread can have multiple documents
- **Thread → Conversations**: One thread can have multiple conversations
- **Document → Vector Chunks**: One document can have multiple vector chunks

#### Foreign Key Constraints
- All foreign keys include `ON DELETE CASCADE` for automatic cleanup
- User-scoped foreign keys ensure data isolation
- Thread-scoped foreign keys maintain thread integrity

### 8. Security Features

#### User Isolation
- All tables include `user_id` foreign key
- RLS policies enforce user-scoped access
- No cross-user data access possible

#### Data Integrity
- Foreign key constraints prevent orphaned records
- Cascade deletion ensures complete cleanup
- Check constraints validate data values

#### Performance Optimization
- Optimized indexes for common queries
- Vector indexes for similarity search
- Composite indexes for multi-column queries 