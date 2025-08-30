# Enhanced Authentication System

## Overview

The RAG application implements a comprehensive authentication system that ensures all Edge Functions require Supabase JWT validation and query user preferences for personalized functionality.

## Architecture

### Authentication Flow

1. **JWT Token Validation**: All Edge Functions validate JWT tokens from Supabase Auth
2. **User Preferences Loading**: After authentication, user preferences are fetched from the database
3. **Resource Ownership Verification**: Ensures users can only access their own data
4. **Audit Logging**: All authentication events are logged for monitoring

### Database Schema

#### User Profiles Table
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### User Preferences Structure
```json
{
  "rag": {
    "default_model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000,
    "include_chat_history": true,
    "cross_thread_search": true,
    "similarity_threshold": 0.7
  },
  "processing": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "max_chunks_per_document": 1000
  },
  "ui": {
    "theme": "light",
    "compact_mode": false,
    "show_sources": true,
    "auto_scroll": true
  },
  "notifications": {
    "email_notifications": false,
    "processing_complete": true,
    "error_alerts": true
  }
}
```

## Edge Function Integration

### Shared Authentication Module

All Edge Functions use a shared authentication module located at `supabase/functions/shared/auth.ts`:

```typescript
import { validateAuthAndGetPreferences, UserPreferences } from '../shared/auth.ts'

// In each Edge Function handler
const { user, preferences, error: authError } = await validateAuthAndGetPreferences(authHeader)

if (authError || !user) {
  return new Response(
    JSON.stringify({ error: authError || 'Authentication failed' }),
    { status: 401, headers: { 'Content-Type': 'application/json' } }
  )
}
```

### Enhanced Edge Functions

#### 1. Vectorize Function (`vectorize/index.ts`)

**Authentication Features:**
- JWT token validation
- User preferences loading for processing settings
- Resource ownership verification
- Audit logging

**User Preferences Usage:**
```typescript
// Use user preferences for vectorization settings
const userChunkSize = preferences?.processing?.chunk_size
const userChunkOverlap = preferences?.processing?.chunk_overlap
const userMaxChunks = preferences?.processing?.max_chunks_per_document

const chunkSize = options?.chunkSize || userChunkSize || VECTORIZATION_CONFIG.DEFAULT_CHUNK_SIZE
```

#### 2. RAG Query Function (`rag-query/index.ts`)

**Authentication Features:**
- JWT token validation
- User preferences loading for RAG settings
- Thread ownership verification
- Cross-thread search based on preferences

**User Preferences Usage:**
```typescript
// Use user preferences for RAG settings
const defaultModel = preferences?.rag?.default_model || 'gpt-4'
const temperature = preferences?.rag?.temperature || 0.7
const includeChatHistory = preferences?.rag?.include_chat_history ?? true
const crossThreadSearch = preferences?.rag?.cross_thread_search ?? true
```

#### 3. Delete Thread Function (`delete-thread/index.ts`)

**Authentication Features:**
- JWT token validation
- User preferences loading for notification settings
- Thread ownership verification
- Confirmation requirement

**User Preferences Usage:**
```typescript
// Use user preferences for notification settings
const emailNotifications = preferences?.notifications?.email_notifications ?? false
const errorAlerts = preferences?.notifications?.error_alerts ?? true
```

## Security Features

### Row Level Security (RLS)

All tables have RLS policies that ensure users can only access their own data:

```sql
-- Example RLS policy for documents
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);
```

### JWT Token Validation

Every Edge Function validates JWT tokens:

```typescript
const { data: { user }, error: authError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''))

if (authError || !user) {
  return { user: null, preferences: {}, error: 'Invalid authentication token' }
}
```

### Resource Ownership Verification

Functions verify that users own the resources they're accessing:

```typescript
// Verify user owns the resource
if (requestData.userId !== user.id) {
  return { error: 'Unauthorized access to resource' }
}
```

## User Preferences System

### Default Preferences

When a user has no preferences set, the system provides sensible defaults:

```typescript
function getDefaultPreferences(): UserPreferences {
  return {
    rag: {
      default_model: 'gpt-4',
      temperature: 0.7,
      max_tokens: 1000,
      include_chat_history: true,
      cross_thread_search: true,
      similarity_threshold: 0.7
    },
    processing: {
      chunk_size: 1000,
      chunk_overlap: 200,
      max_chunks_per_document: 1000
    },
    // ... other defaults
  }
}
```

### Preference Categories

#### RAG Settings
- **default_model**: Preferred AI model for responses
- **temperature**: Creativity level for responses
- **max_tokens**: Maximum response length
- **include_chat_history**: Whether to include chat history in context
- **cross_thread_search**: Whether to search across multiple threads
- **similarity_threshold**: Minimum similarity for relevant results

#### Processing Settings
- **chunk_size**: Document chunk size for vectorization
- **chunk_overlap**: Overlap between chunks
- **max_chunks_per_document**: Maximum chunks per document

#### UI Settings
- **theme**: Light or dark theme preference
- **compact_mode**: Compact interface mode
- **show_sources**: Whether to show source attribution
- **auto_scroll**: Auto-scroll to new messages

#### Notification Settings
- **email_notifications**: Email notification preferences
- **processing_complete**: Notify when processing completes
- **error_alerts**: Alert on errors

## Database Functions

### Get User Preferences

```sql
CREATE OR REPLACE FUNCTION get_user_preferences(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    user_prefs JSONB;
BEGIN
    SELECT preferences INTO user_prefs
    FROM user_profiles
    WHERE user_id = p_user_id;
    
    IF user_prefs IS NULL THEN
        user_prefs := '{"rag": {...}, "processing": {...}}'::JSONB;
    END IF;
    
    RETURN user_prefs;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Update User Preferences

```sql
CREATE OR REPLACE FUNCTION update_user_preferences(
    p_user_id UUID,
    p_preferences JSONB
)
RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO user_profiles (user_id, preferences, updated_at)
    VALUES (p_user_id, p_preferences, NOW())
    ON CONFLICT (user_id)
    DO UPDATE SET 
        preferences = p_preferences,
        updated_at = NOW();
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Monitoring and Logging

### Authentication Events

All authentication events are logged with structured information:

```typescript
logAuthEvent('login_success', userId, { timestamp: new Date().toISOString() })
logAuthEvent('resource_access', userId, { resource: 'document', action: 'read' })
logAuthEvent('preferences_updated', userId, { category: 'rag' })
```

### Error Handling

Comprehensive error handling ensures graceful degradation:

```typescript
try {
  const { user, preferences, error } = await validateAuthAndGetPreferences(authHeader)
  if (error) {
    // Log error and return appropriate response
    console.error(`[AUTH] Authentication failed:`, error)
    return new Response(JSON.stringify({ error }), { status: 401 })
  }
} catch (error) {
  console.error(`[AUTH] Unexpected error:`, error)
  return new Response(JSON.stringify({ error: 'Internal server error' }), { status: 500 })
}
```

## Frontend Integration

### Authentication State Management

The frontend manages authentication state and user preferences:

```typescript
// src/lib/supabase.ts
export const auth = {
  getCurrentUser: async () => {
    const { data: { user }, error } = await supabase.auth.getUser()
    return { user, error }
  },
  
  getUserPreferences: async () => {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return null
    
    const { data, error } = await supabase
      .rpc('get_user_preferences', { p_user_id: user.id })
    
    return { data, error }
  }
}
```

### Preference Updates

Users can update their preferences through the UI:

```typescript
export const updatePreferences = async (preferences: Partial<UserPreferences>) => {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('User not authenticated')
  
  const { error } = await supabase
    .rpc('update_user_preferences', { 
      p_user_id: user.id, 
      p_preferences: preferences 
    })
  
  if (error) throw error
}
```

## Deployment Considerations

### Environment Variables

Ensure all required environment variables are set:

```bash
# Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI (for Edge Functions)
OPENAI_API_KEY=your-openai-api-key
```

### Database Migrations

Run migrations in order:

```bash
# Apply all migrations including user preferences
supabase db push
```

### Edge Function Deployment

Deploy all Edge Functions with the shared auth module:

```bash
supabase functions deploy vectorize
supabase functions deploy rag-query
supabase functions deploy delete-thread
```

## Testing

### Authentication Tests

Test authentication flows:

```typescript
// Test valid JWT
const validToken = 'valid-jwt-token'
const result = await validateAuthAndGetPreferences(`Bearer ${validToken}`)
expect(result.user).toBeTruthy()
expect(result.preferences).toBeDefined()

// Test invalid JWT
const invalidToken = 'invalid-token'
const result = await validateAuthAndGetPreferences(`Bearer ${invalidToken}`)
expect(result.error).toBe('Invalid authentication token')
```

### Preference Tests

Test user preference functionality:

```typescript
// Test default preferences
const result = await validateAuthAndGetPreferences(validToken)
expect(result.preferences.rag.default_model).toBe('gpt-4')

// Test preference updates
const success = await updateUserPreferences(userId, { rag: { temperature: 0.8 } })
expect(success).toBe(true)
```

## Security Best Practices

1. **Always validate JWT tokens** before processing requests
2. **Verify resource ownership** for all data access
3. **Use RLS policies** to enforce data isolation
4. **Log authentication events** for monitoring
5. **Handle errors gracefully** without exposing sensitive information
6. **Use secure defaults** for user preferences
7. **Validate input data** before processing
8. **Implement rate limiting** to prevent abuse

## Troubleshooting

### Common Issues

1. **Authentication failures**: Check JWT token validity and expiration
2. **Preference loading errors**: Verify database functions and RLS policies
3. **Resource access denied**: Ensure proper user ownership verification
4. **Edge Function errors**: Check environment variables and deployment

### Debug Steps

1. Check Edge Function logs for authentication errors
2. Verify JWT token format and expiration
3. Test database functions directly
4. Validate RLS policies are working correctly
5. Check environment variable configuration

This enhanced authentication system provides comprehensive security while enabling personalized user experiences through preferences management. 