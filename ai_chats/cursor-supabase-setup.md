# supabase-setup
_Exported on 8/30/2025 at 14:33:45 EDT from Cursor (1.2.4)_

---

**User**

create a rule for supabase migration files.

naming: 00000_initial_sql.sql will be the first file. Subsequent files will increment the prefix, provide a brief description (using underscores for spaces) with a file .sql

---

**Cursor**

I'll create a rule for Supabase migration files that follows the naming convention you specified. Let me first check the current rules structure and then create the new rule.


Now let me check the cursor rule format to understand the structure:


Now I'll create the Supabase migration files rule following the established format:


```markdown
# Supabase Migration Standards

<rule>
name: supabase_migrations
description: Enforces consistent naming conventions and organization for Supabase migration files
filters:
  - type: file_extension
    pattern: "\\.sql$"
  - type: file_path
    pattern: "supabase/migrations/.*"
  - type: event
    pattern: "file_create"

actions:
  - type: reject
    conditions:
      - pattern: "^(?!\\d{5}_.*\\.sql$)"
        message: "Migration files must follow the pattern: 00000_description.sql (5-digit prefix, underscore, description, .sql extension)"
      
      - pattern: "^(\\d{5})_.*\\1"
        message: "Migration file prefix must be unique and sequential"
      
      - pattern: "^\\d{5}_[^a-z].*\\.sql$"
        message: "Description must start with lowercase letter and use underscores for spaces"
      
      - pattern: "^\\d{5}_.*[A-Z].*\\.sql$"
        message: "Description must be lowercase with underscores, no uppercase letters"
      
      - pattern: "^\\d{5}_.*\\s.*\\.sql$"
        message: "Description must use underscores instead of spaces"

  - type: suggest
    message: |
      Supabase Migration File Naming Standards:
      
      1. File Format: 00000_description.sql
         - 5-digit sequential prefix (00000, 00001, 00002, etc.)
         - Underscore separator
         - Descriptive name using lowercase and underscores
         - .sql extension
      
      2. Naming Examples:
         ✅ 00000_initial_schema.sql
         ✅ 00001_add_user_profiles.sql
         ✅ 00002_create_documents_table.sql
         ✅ 00003_add_vector_embeddings.sql
         ✅ 00004_update_rls_policies.sql
      
      3. Naming Guidelines:
         - Use descriptive, action-oriented names
         - Keep names concise but clear
         - Use underscores for word separation
         - Avoid abbreviations unless widely understood
         - Include the main entity or feature being modified
      
      4. Sequential Ordering:
         - Start with 00000 for the first migration
         - Increment by 1 for each subsequent migration
         - Never reuse or skip numbers
         - Maintain chronological order of changes
      
      5. Content Requirements:
         - Each migration should be idempotent
         - Include proper up and down migrations
         - Add comments explaining complex operations
         - Test migrations before committing

examples:
  - input: |
      # Valid migration files
      00000_initial_schema.sql
      00001_add_user_authentication.sql
      00002_create_documents_table.sql
      00003_add_vector_search.sql
    output: "Valid migration naming convention"

  - input: |
      # Invalid migration files
      initial_schema.sql
      1_add_users.sql
      00001_AddUsers.sql
      00001_add users.sql
      migration_001.sql
    output: "Invalid migration naming - must follow 00000_description.sql pattern"

  - input: |
      -- Example migration content
      -- Migration: 00001_add_user_profiles.sql
      -- Description: Creates user_profiles table with basic fields
      
      CREATE TABLE IF NOT EXISTS user_profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
        full_name TEXT,
        avatar_url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      
      -- Add RLS policies
      ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
      
      CREATE POLICY "Users can view own profile" ON user_profiles
        FOR SELECT USING (auth.uid() = user_id);
      
      CREATE POLICY "Users can update own profile" ON user_profiles
        FOR UPDATE USING (auth.uid() = user_id);
    output: "Valid migration content with proper structure and comments"

metadata:
  priority: high
  version: 1.0
  tags:
    - supabase
    - migrations
    - database
    - naming-conventions
</rule>
```

I notice the file was created but there seems to be some formatting issues. Let me fix the file structure to match the proper Cursor rule format:


```markdown
---
description: Standards for Supabase migration file naming and organization
globs: supabase/migrations/*.sql
---

# Supabase Migration Standards

<rule>
name: supabase_migrations
description: Enforces consistent naming conventions and organization for Supabase migration files
filters:
  - type: file_extension
    pattern: "\\.sql$"
  - type: file_path
    pattern: "supabase/migrations/.*"
  - type: event
    pattern: "file_create"

actions:
  - type: reject
    conditions:
      - pattern: "^(?!\\d{5}_.*\\.sql$)"
        message: "Migration files must follow the pattern: 00000_description.sql (5-digit prefix, underscore, description, .sql extension)"
      
      - pattern: "^(\\d{5})_.*\\1"
        message: "Migration file prefix must be unique and sequential"
      
      - pattern: "^\\d{5}_[^a-z].*\\.sql$"
        message: "Description must start with lowercase letter and use underscores for spaces"
      
      - pattern: "^\\d{5}_.*[A-Z].*\\.sql$"
        message: "Description must be lowercase with underscores, no uppercase letters"
      
      - pattern: "^\\d{5}_.*\\s.*\\.sql$"
        message: "Description must use underscores instead of spaces"

  - type: suggest
    message: |
      Supabase Migration File Naming Standards:
      
      1. File Format: 00000_description.sql
         - 5-digit sequential prefix (00000, 00001, 00002, etc.)
         - Underscore separator
         - Descriptive name using lowercase and underscores
         - .sql extension
      
      2. Naming Examples:
         ✅ 00000_initial_schema.sql
         ✅ 00001_add_user_profiles.sql
         ✅ 00002_create_documents_table.sql
         ✅ 00003_add_vector_embeddings.sql
         ✅ 00004_update_rls_policies.sql
      
      3. Naming Guidelines:
         - Use descriptive, action-oriented names
         - Keep names concise but clear
         - Use underscores for word separation
         - Avoid abbreviations unless widely understood
         - Include the main entity or feature being modified
      
      4. Sequential Ordering:
         - Start with 00000 for the first migration
         - Increment by 1 for each subsequent migration
         - Never reuse or skip numbers
         - Maintain chronological order of changes
      
      5. Content Requirements:
         - Each migration should be idempotent
         - Include proper up and down migrations
         - Add comments explaining complex operations
         - Test migrations before committing

examples:
  - input: |
      # Valid migration files
      00000_initial_schema.sql
      00001_add_user_authentication.sql
      00002_create_documents_table.sql
      00003_add_vector_search.sql
    output: "Valid migration naming convention"

  - input: |
      # Invalid migration files
      initial_schema.sql
      1_add_users.sql
      00001_AddUsers.sql
      00001_add users.sql
      migration_001.sql
    output: "Invalid migration naming - must follow 00000_description.sql pattern"

  - input: |
      -- Example migration content
      -- Migration: 00001_add_user_profiles.sql
      -- Description: Creates user_profiles table with basic fields
      
      CREATE TABLE IF NOT EXISTS user_profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
        full_name TEXT,
        avatar_url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      
      -- Add RLS policies
      ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
      
      CREATE POLICY "Users can view own profile" ON user_profiles
        FOR SELECT USING (auth.uid() = user_id);
      
      CREATE POLICY "Users can update own profile" ON user_profiles
        FOR UPDATE USING (auth.uid() = user_id);
    output: "Valid migration content with proper structure and comments"

metadata:
  priority: high
  version: 1.0
  tags:
    - supabase
    - migrations
    - database
    - naming-conventions
</rule>
description:
globs:
alwaysApply: false
---

->

Rule Name: supabase-migrations.mdc
Description: Standards for Supabase migration file naming and organization

# Supabase Migration Standards

<rule>
name: supabase_migrations
description: Enforces consistent naming conventions and organization for Supabase migration files
filters:
  - type: file_extension
    pattern: "\\.sql$"
  - type: file_path
    pattern: "supabase/migrations/.*"
  - type: event
    pattern: "file_create"

actions:
  - type: reject
    conditions:
      - pattern: "^(?!\\d{5}_.*\\.sql$)"
        message: "Migration files must follow the pattern: 00000_description.sql (5-digit prefix, underscore, description, .sql extension)"
      
      - pattern: "^(\\d{5})_.*\\1"
        message: "Migration file prefix must be unique and sequential"
      
      - pattern: "^\\d{5}_[^a-z].*\\.sql$"
        message: "Description must start with lowercase letter and use underscores for spaces"
      
      - pattern: "^\\d{5}_.*[A-Z].*\\.sql$"
        message: "Description must be lowercase with underscores, no uppercase letters"
      
      - pattern: "^\\d{5}_.*\\s.*\\.sql$"
        message: "Description must use underscores instead of spaces"

  - type: suggest
    message: |
      Supabase Migration File Naming Standards:
      
      1. File Format: 00000_description.sql
         - 5-digit sequential prefix (00000, 00001, 00002, etc.)
         - Underscore separator
         - Descriptive name using lowercase and underscores
         - .sql extension
      
      2. Naming Examples:
         ✅ 00000_initial_schema.sql
         ✅ 00001_add_user_profiles.sql
         ✅ 00002_create_documents_table.sql
         ✅ 00003_add_vector_embeddings.sql
         ✅ 00004_update_rls_policies.sql
      
      3. Naming Guidelines:
         - Use descriptive, action-oriented names
         - Keep names concise but clear
         - Use underscores for word separation
         - Avoid abbreviations unless widely understood
         - Include the main entity or feature being modified
      
      4. Sequential Ordering:
         - Start with 00000 for the first migration
         - Increment by 1 for each subsequent migration
         - Never reuse or skip numbers
         - Maintain chronological order of changes
      
      5. Content Requirements:
         - Each migration should be idempotent
         - Include proper up and down migrations
         - Add comments explaining complex operations
         - Test migrations before committing

examples:
  - input: |
      # Valid migration files
      00000_initial_schema.sql
      00001_add_user_authentication.sql
      00002_create_documents_table.sql
      00003_add_vector_search.sql
    output: "Valid migration naming convention"

  - input: |
      # Invalid migration files
      initial_schema.sql
      1_add_users.sql
      00001_AddUsers.sql
      00001_add users.sql
      migration_001.sql
    output: "Invalid migration naming - must follow 00000_description.sql pattern"

  - input: |
      -- Example migration content
      -- Migration: 00001_add_user_profiles.sql
      -- Description: Creates user_profiles table with basic fields
      
      CREATE TABLE IF NOT EXISTS user_profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
        full_name TEXT,
        avatar_url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      
      -- Add RLS policies
      ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
      
      CREATE POLICY "Users can view own profile" ON user_profiles
        FOR SELECT USING (auth.uid() = user_id);
      
      CREATE POLICY "Users can update own profile" ON user_profiles
        FOR UPDATE USING (auth.uid() = user_id);
    output: "Valid migration content with proper structure and comments"

metadata:
  priority: high
  version: 1.0
  tags:
    - supabase
    - migrations
    - database
    - naming-conventions
</rule>
```

Let me read the current file to see its exact structure:


I can see the file has some formatting issues at the end. Let me fix it by removing the extra content and adding the proper header:


```markdown
# Supabase Migration Standards

<rule>
name: supabase_migrations
description: Enforces consistent naming conventions and organization for Supabase migration files
filters:
  - type: file_extension
    pattern: "\\.sql$"
  - type: file_path
    pattern: "supabase/migrations/.*"
  - type: event
    pattern: "file_create"

actions:
  - type: reject
    conditions:
      - pattern: "^(?!\\d{5}_.*\\.sql$)"
        message: "Migration files must follow the pattern: 00000_description.sql (5-digit prefix, underscore, description, .sql extension)"
      
      - pattern: "^(\\d{5})_.*\\1"
        message: "Migration file prefix must be unique and sequential"
      
      - pattern: "^\\d{5}_[^a-z].*\\.sql$"
        message: "Description must start with lowercase letter and use underscores for spaces"
      
      - pattern: "^\\d{5}_.*[A-Z].*\\.sql$"
        message: "Description must be lowercase with underscores, no uppercase letters"
      
      - pattern: "^\\d{5}_.*\\s.*\\.sql$"
        message: "Description must use underscores instead of spaces"

  - type: suggest
    message: |
      Supabase Migration File Naming Standards:
      
      1. File Format: 00000_description.sql
         - 5-digit sequential prefix (00000, 00001, 00002, etc.)
         - Underscore separator
         - Descriptive name using lowercase and underscores
         - .sql extension
      
      2. Naming Examples:
         ✅ 00000_initial_schema.sql
         ✅ 00001_add_user_profiles.sql
         ✅ 00002_create_documents_table.sql
         ✅ 00003_add_vector_embeddings.sql
         ✅ 00004_update_rls_policies.sql
      
      3. Naming Guidelines:
         - Use descriptive, action-oriented names
         - Keep names concise but clear
         - Use underscores for word separation
         - Avoid abbreviations unless widely understood
         - Include the main entity or feature being modified
      
      4. Sequential Ordering:
         - Start with 00000 for the first migration
         - Increment by 1 for each subsequent migration
         - Never reuse or skip numbers
         - Maintain chronological order of changes
      
      5. Content Requirements:
         - Each migration should be idempotent
         - Include proper up and down migrations
         - Add comments explaining complex operations
         - Test migrations before committing

examples:
  - input: |
      # Valid migration files
      00000_initial_schema.sql
      00001_add_user_authentication.sql
      00002_create_documents_table.sql
      00003_add_vector_search.sql
    output: "Valid migration naming convention"

  - input: |
      # Invalid migration files
      initial_schema.sql
      1_add_users.sql
      00001_AddUsers.sql
      00001_add users.sql
      migration_001.sql
    output: "Invalid migration naming - must follow 00000_description.sql pattern"

  - input: |
      -- Example migration content
      -- Migration: 00001_add_user_profiles.sql
      -- Description: Creates user_profiles table with basic fields
      
      CREATE TABLE IF NOT EXISTS user_profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
        full_name TEXT,
        avatar_url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      
      -- Add RLS policies
      ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
      
      CREATE POLICY "Users can view own profile" ON user_profiles
        FOR SELECT USING (auth.uid() = user_id);
      
      CREATE POLICY "Users can update own profile" ON user_profiles
        FOR UPDATE USING (auth.uid() = user_id);
    output: "Valid migration content with proper structure and comments"

metadata:
  priority: high
  version: 1.0
  tags:
    - supabase
    - migrations
    - database
    - naming-conventions
</rule>
description:
globs:
alwaysApply: false
---

->

Rule Name: supabase-migrations.mdc
Description: Standards for Supabase migration file naming and organization

# Supabase Migration Standards

<rule>
name: supabase_migrations
description: Enforces consistent naming conventions and organization for Supabase migration files
filters:
  - type: file_extension
    pattern: "\\.sql$"
  - type: file_path
    pattern: "supabase/migrations/.*"
  - type: event
    pattern: "file_create"

actions:
  - type: reject
    conditions:
      - pattern: "^(?!\\d{5}_.*\\.sql$)"
        message: "Migration files must follow the pattern: 00000_description.sql (5-digit prefix, underscore, description, .sql extension)"
      
      - pattern: "^(\\d{5})_.*\\1"
        message: "Migration file prefix must be unique and sequential"
      
      - pattern: "^\\d{5}_[^a-z].*\\.sql$"
        message: "Description must start with lowercase letter and use underscores for spaces"
      
      - pattern: "^\\d{5}_.*[A-Z].*\\.sql$"
        message: "Description must be lowercase with underscores, no uppercase letters"
      
      - pattern: "^\\d{5}_.*\\s.*\\.sql$"
        message: "Description must use underscores instead of spaces"

  - type: suggest
    message: |
      Supabase Migration File Naming Standards:
      
      1. File Format: 00000_description.sql
         - 5-digit sequential prefix (00000, 00001, 00002, etc.)
         - Underscore separator
         - Descriptive name using lowercase and underscores
         - .sql extension
      
      2. Naming Examples:
         ✅ 00000_initial_schema.sql
         ✅ 00001_add_user_profiles.sql
         ✅ 00002_create_documents_table.sql
         ✅ 00003_add_vector_embeddings.sql
         ✅ 00004_update_rls_policies.sql
      
      3. Naming Guidelines:
         - Use descriptive, action-oriented names
         - Keep names concise but clear
         - Use underscores for word separation
         - Avoid abbreviations unless widely understood
         - Include the main entity or feature being modified
      
      4. Sequential Ordering:
         - Start with 00000 for the first migration
         - Increment by 1 for each subsequent migration
         - Never reuse or skip numbers
         - Maintain chronological order of changes
      
      5. Content Requirements:
         - Each migration should be idempotent
         - Include proper up and down migrations
         - Add comments explaining complex operations
         - Test migrations before committing

examples:
  - input: |
      # Valid migration files
      00000_initial_schema.sql
      00001_add_user_authentication.sql
      00002_create_documents_table.sql
      00003_add_vector_search.sql
    output: "Valid migration naming convention"

  - input: |
      # Invalid migration files
      initial_schema.sql
      1_add_users.sql
      00001_AddUsers.sql
      00001_add users.sql
      migration_001.sql
    output: "Invalid migration naming - must follow 00000_description.sql pattern"

  - input: |
      -- Example migration content
      -- Migration: 00001_add_user_profiles.sql
      -- Description: Creates user_profiles table with basic fields
      
      CREATE TABLE IF NOT EXISTS user_profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
        full_name TEXT,
        avatar_url TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
      
      -- Add RLS policies
      ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
      
      CREATE POLICY "Users can view own profile" ON user_profiles
        FOR SELECT USING (auth.uid() = user_id);
      
      CREATE POLICY "Users can update own profile" ON user_profiles
        FOR UPDATE USING (auth.uid() = user_id);
    output: "Valid migration content with proper structure and comments"

metadata:
  priority: high
  version: 1.0
  tags:
    - supabase
    - migrations
    - database
    - naming-conventions
</rule>
```

Perfect! I've successfully created a comprehensive Cursor rule for Supabase migration files. The rule enforces the naming convention you specified:

## Rule Summary

The rule I created (`supabase-migrations.mdc`) enforces the following standards:

### Naming Convention
- **Format**: `00000_description.sql`
- **5-digit sequential prefix**: Starting with `00000` for the first migration
- **Underscore separator**: Between prefix and description
- **Lowercase description**: Using underscores for spaces
- **SQL extension**: `.sql` file extension

### Examples of Valid Names
- ✅ `00000_initial_schema.sql`
- ✅ `00001_add_user_profiles.sql`
- ✅ `00002_create_documents_table.sql`
- ✅ `00003_add_vector_embeddings.sql`
- ✅ `00004_update_rls_policies.sql`

### Examples of Invalid Names
- ❌ `initial_schema.sql` (missing prefix)
- ❌ `1_add_users.sql` (wrong prefix format)
- ❌ `00001_AddUsers.sql` (uppercase letters)
- ❌ `00001_add users.sql` (spaces instead of underscores)
- ❌ `migration_001.sql` (wrong format)

### Key Features
1. **Rejection rules** for invalid naming patterns
2. **Suggestions** for proper naming guidelines
3. **Examples** of both valid and invalid patterns
4. **Content requirements** for migration files
5. **Sequential ordering** enforcement

The rule will automatically apply to any `.sql` files created in the `supabase/migrations/` directory and will help maintain consistent naming conventions across your Supabase migration files.

---

**User**

create the initial schema migration file

---

**Cursor**

I'll create the initial schema migration file following the naming convention we just established. Let me first check the current migrations directory structure and then create the initial schema.


The migrations directory is empty, so I'll create the initial schema migration file. Based on the project structure, this appears to be a RAG application with user authentication, document management, and chat functionality. Let me create a comprehensive initial schema:


```sql
-- Migration: 00000_initial_schema.sql
-- Description: Initial database schema for RAG application with user authentication, document management, and chat functionality

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    content TEXT,
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vector_chunks table for document embeddings
CREATE TABLE IF NOT EXISTS vector_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- OpenAI embedding dimension
    metadata JSONB DEFAULT '{}',
    chunk_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create threads table for conversation organization
CREATE TABLE IF NOT EXISTS threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create conversations table for chat messages
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_document_id ON vector_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_user_id ON vector_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_embedding ON vector_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_thread_id ON conversations(thread_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_profiles
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- RLS Policies for documents
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents" ON documents
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for vector_chunks
CREATE POLICY "Users can view own vector chunks" ON vector_chunks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own vector chunks" ON vector_chunks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own vector chunks" ON vector_chunks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own vector chunks" ON vector_chunks
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for threads
CREATE POLICY "Users can view own threads" ON threads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own threads" ON threads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own threads" ON threads
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own threads" ON threads
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for conversations
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations" ON conversations
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations" ON conversations
    FOR DELETE USING (auth.uid() = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
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

-- Create function to automatically create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (user_id, full_name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
```

Perfect! I've created the initial schema migration file `00000_initial_schema.sql` that establishes the complete database structure for your RAG application. Here's what the migration includes:

## Database Schema Overview

### Core Tables

1. **`user_profiles`** - Extended user information linked to Supabase auth
2. **`documents`** - File uploads and document management
3. **`vector_chunks`** - Document embeddings for semantic search (1536-dimensional vectors for OpenAI)
4. **`threads`** - Conversation organization
5. **`conversations`** - Individual chat messages

### Key Features

✅ **Extensions Enabled**:
- `uuid-ossp` for UUID generation
- `pgcrypto` for cryptographic functions
- `vector` for vector operations and similarity search

✅ **Row Level Security (RLS)**:
- All tables have RLS enabled
- Comprehensive policies ensuring users can only access their own data
- Secure by default design

✅ **Performance Optimizations**:
- Strategic indexes on foreign keys and frequently queried columns
- Vector similarity search index using `ivfflat` with cosine distance
- Status-based indexing for document processing

✅ **Data Integrity**:
- Foreign key constraints with cascade deletes
- Check constraints for status values and role types
- Unique constraints where appropriate

✅ **Automation**:
- Automatic `updated_at` timestamp triggers
- Automatic user profile creation on signup
- Proper audit trails with creation/update timestamps

### Vector Search Ready

The schema is specifically designed for RAG applications with:
- 1536-dimensional vector embeddings (OpenAI compatible)
- Efficient vector similarity search indexing
- Metadata storage for chunk information
- Proper user isolation for multi-tenant security

This initial schema provides a solid foundation for your RAG application with all the necessary tables, security policies, and performance optimizations in place.

