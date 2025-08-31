# RAGged Security & Scoping Guide

Comprehensive security guide for the RAGged application, covering user isolation, data privacy, Row Level Security (RLS), and security best practices.

## Table of Contents

- [Security Overview](#security-overview)
- [User Isolation & Scoping](#user-isolation--scoping)
- [Row Level Security (RLS)](#row-level-security-rls)
- [Authentication & Authorization](#authentication--authorization)
- [Data Privacy](#data-privacy)
- [API Security](#api-security)
- [Storage Security](#storage-security)
- [Edge Function Security](#edge-function-security)
- [Multi-Tenant Architecture](#multi-tenant-architecture)
- [Security Best Practices](#security-best-practices)
- [Compliance](#compliance)

---

## Security Overview

### Security Model

The RAGged application implements a **multi-layered security approach**:

1. **Authentication**: JWT-based authentication via Supabase Auth
2. **Authorization**: Row Level Security (RLS) policies
3. **Data Isolation**: Complete user-scoped data separation
4. **API Security**: Rate limiting and input validation
5. **Storage Security**: User-scoped file storage with RLS
6. **Network Security**: HTTPS/TLS encryption

### Security Principles

- **Zero Trust**: Never trust, always verify
- **Principle of Least Privilege**: Users only access their own data
- **Defense in Depth**: Multiple security layers
- **Data Privacy by Design**: Privacy built into architecture
- **Secure by Default**: Secure configurations out of the box

---

## User Isolation & Scoping

### User Data Isolation

Every piece of data in the application is **strictly scoped to individual users**:

```sql
-- All tables include user_id for isolation
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- User scoping
  title TEXT NOT NULL,
  -- ... other fields
);

CREATE TABLE threads (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- User scoping
  title TEXT NOT NULL,
  -- ... other fields
);

CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- User scoping
  -- ... other fields
);

CREATE TABLE vector_chunks (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- User scoping
  -- ... other fields
);
```

### Multi-Thread Support with Isolation

Users can create **multiple threads** while maintaining complete isolation:

```javascript
// Each thread is isolated to the user
const userThreads = await supabase
  .from('threads')
  .select('*')
  .eq('user_id', userId) // Only user's threads
  .order('updated_at', { ascending: false })

// Thread-specific documents
const threadDocuments = await supabase
  .from('documents')
  .select('*')
  .eq('thread_id', threadId)
  .eq('user_id', userId) // Double-check user ownership
```

### Cross-Thread Search Security

Cross-thread search maintains user isolation:

```javascript
// Cross-thread search only searches user's own threads
const response = await supabase.functions.invoke('rag-query', {
  body: {
    threadId: currentThreadId,
    userId: userId, // Required for user scoping
    query: 'Search across my threads',
    crossThreadSearch: true,
    maxThreadsSearch: 5 // Limited scope
  }
})
```

---

## Row Level Security (RLS)

### RLS Policy Implementation

All tables implement comprehensive RLS policies:

```sql
-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_chunks ENABLE ROW LEVEL SECURITY;
```

### Document Table Policies

```sql
-- Users can only view their own documents
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own documents
CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own documents
CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own documents
CREATE POLICY "Users can delete own documents" ON documents
    FOR DELETE USING (auth.uid() = user_id);
```

### Thread Table Policies

```sql
-- Users can only access their own threads
CREATE POLICY "Users can view own threads" ON threads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own threads" ON threads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own threads" ON threads
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own threads" ON threads
    FOR DELETE USING (auth.uid() = user_id);
```

### Conversation Table Policies

```sql
-- Users can only access conversations in their own threads
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

### Vector Chunks Table Policies

```sql
-- Users can only access vector chunks from their own documents
CREATE POLICY "Users can view own vector chunks" ON vector_chunks
    FOR SELECT USING (
        auth.uid() = user_id AND
        document_id IN (
            SELECT id FROM documents WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own vector chunks" ON vector_chunks
    FOR INSERT WITH CHECK (
        auth.uid() = user_id AND
        document_id IN (
            SELECT id FROM documents WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own vector chunks" ON vector_chunks
    FOR UPDATE USING (
        auth.uid() = user_id AND
        document_id IN (
            SELECT id FROM documents WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own vector chunks" ON vector_chunks
    FOR DELETE USING (
        auth.uid() = user_id AND
        document_id IN (
            SELECT id FROM documents WHERE user_id = auth.uid()
        )
    );
```

### RLS Policy Verification

```sql
-- Verify RLS policies are active
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    CASE 
        WHEN rowsecurity THEN 'Enabled'
        ELSE 'Disabled'
    END as rls_status
FROM pg_tables 
WHERE schemaname = 'public'
AND tablename IN ('documents', 'threads', 'conversations', 'vector_chunks');

-- Check policy details
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

---

## Authentication & Authorization

### JWT Token Management

```javascript
// Initialize Supabase client with authentication
const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
)

// Get current user session
const { data: { session }, error } = await supabase.auth.getSession()

if (!session) {
  throw new Error('Authentication required')
}

const userId = session.user.id
```

### Session Management

```javascript
// Automatic session refresh
async function refreshSession() {
  const { data, error } = await supabase.auth.refreshSession()
  
  if (error) {
    console.error('Session refresh failed:', error)
    // Redirect to login
    window.location.href = '/login'
    return false
  }
  
  return true
}

// Check session before operations
async function checkAndRefreshSession() {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    return await refreshSession()
  }
  
  // Check if token expires soon (within 5 minutes)
  const expiresAt = new Date(session.expires_at * 1000)
  const now = new Date()
  const fiveMinutes = 5 * 60 * 1000
  
  if (expiresAt.getTime() - now.getTime() < fiveMinutes) {
    return await refreshSession()
  }
  
  return true
}
```

### Service Role Access

Edge Functions use service role for database operations:

```javascript
// Edge Functions use service role key
const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')! // Service role, not anon key
)

// Always verify user ownership in Edge Functions
async function verifyUserOwnership(userId: string, resourceId: string, table: string) {
  const { data, error } = await supabase
    .from(table)
    .select('id')
    .eq('id', resourceId)
    .eq('user_id', userId)
    .single()
  
  if (error || !data) {
    throw new Error('Access denied: Resource not found or access denied')
  }
  
  return data
}
```

---

## Data Privacy

### Data Minimization

The application follows **data minimization principles**:

```javascript
// Only collect necessary user data
const userProfile = {
  id: user.id,
  email: user.email,
  full_name: user.user_metadata?.full_name || null,
  // No unnecessary personal data
}

// Document metadata is minimal
const documentMetadata = {
  file_name: file.name,
  file_size: file.size,
  file_type: file.type,
  uploaded_at: new Date().toISOString(),
  // No content analysis or personal data extraction
}
```

### Data Retention

```sql
-- Implement data retention policies
-- Archive old conversations after 90 days
CREATE OR REPLACE FUNCTION archive_old_conversations()
RETURNS void AS $$
BEGIN
  INSERT INTO conversation_archives (
    conversation_id,
    thread_id,
    user_id,
    content,
    role,
    created_at,
    archived_at
  )
  SELECT 
    id,
    thread_id,
    user_id,
    content,
    role,
    created_at,
    NOW()
  FROM conversations
  WHERE created_at < NOW() - INTERVAL '90 days';
  
  DELETE FROM conversations 
  WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Schedule retention job
SELECT cron.schedule(
  'archive-old-conversations',
  '0 2 * * *', -- Daily at 2 AM
  'SELECT archive_old_conversations();'
);
```

### Data Encryption

```javascript
// Encrypt sensitive data at rest
import { encrypt, decrypt } from 'crypto-js'

// Encrypt document content before storage
function encryptContent(content: string, key: string): string {
  return encrypt(content, key).toString()
}

// Decrypt content when needed
function decryptContent(encryptedContent: string, key: string): string {
  const bytes = decrypt(encryptedContent, key)
  return bytes.toString(CryptoJS.enc.Utf8)
}

// Use in document processing
const encryptedContent = encryptContent(documentContent, encryptionKey)
await supabase
  .from('documents')
  .update({ content: encryptedContent })
  .eq('id', documentId)
```

### Data Anonymization

```javascript
// Anonymize user data for analytics
function anonymizeUserData(userData: any) {
  return {
    user_id_hash: hash(userData.id), // One-way hash
    document_count: userData.document_count,
    thread_count: userData.thread_count,
    created_at: userData.created_at,
    // No personally identifiable information
  }
}
```

---

## API Security

### Input Validation

```typescript
// Comprehensive input validation
interface ValidationRules {
  maxFileSize: number
  allowedFileTypes: string[]
  maxQueryLength: number
  maxThreadsPerUser: number
}

const validationRules: ValidationRules = {
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedFileTypes: ['application/pdf', 'text/plain', 'application/rtf'],
  maxQueryLength: 1000,
  maxThreadsPerUser: 100
}

function validateFileUpload(file: File): boolean {
  if (file.size > validationRules.maxFileSize) {
    throw new Error('File too large')
  }
  
  if (!validationRules.allowedFileTypes.includes(file.type)) {
    throw new Error('File type not allowed')
  }
  
  return true
}

function validateQuery(query: string): boolean {
  if (query.length > validationRules.maxQueryLength) {
    throw new Error('Query too long')
  }
  
  // Check for malicious content
  if (containsMaliciousContent(query)) {
    throw new Error('Query contains disallowed content')
  }
  
  return true
}
```

### Rate Limiting

```javascript
// Implement rate limiting
const rateLimiter = {
  requests: new Map(),
  
  checkLimit: (userId: string, limit: number = 100, window: number = 60000) => {
    const now = Date.now()
    const userRequests = rateLimiter.requests.get(userId) || []
    
    // Remove old requests
    const recentRequests = userRequests.filter(time => now - time < window)
    
    if (recentRequests.length >= limit) {
      return false
    }
    
    recentRequests.push(now)
    rateLimiter.requests.set(userId, recentRequests)
    return true
  }
}

// Use in API endpoints
app.post('/api/rag-query', async (req, res) => {
  const userId = req.user.id
  
  if (!rateLimiter.checkLimit(userId, 50, 60000)) { // 50 requests per minute
    return res.status(429).json({ error: 'Rate limit exceeded' })
  }
  
  // Process request
})
```

### CORS Configuration

```javascript
// Secure CORS configuration
const corsOptions = {
  origin: [
    'https://your-domain.com',
    'https://app.your-domain.com'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Client-Info',
    'X-API-Key'
  ],
  maxAge: 86400 // 24 hours
}

app.use(cors(corsOptions))
```

### API Key Security

```javascript
// Secure API key handling
function validateApiKey(apiKey: string): boolean {
  if (!apiKey || typeof apiKey !== 'string') {
    return false
  }
  
  if (!apiKey.startsWith('sk-')) {
    return false
  }
  
  if (apiKey.length < 20) {
    return false
  }
  
  return true
}

// Use in Edge Functions
const openaiApiKey = Deno.env.get('OPENAI_API_KEY')
if (!validateApiKey(openaiApiKey)) {
  throw new Error('Invalid OpenAI API key')
}
```

---

## Storage Security

### File Upload Security

```javascript
// Secure file upload validation
function validateFileUpload(file: File, userId: string): boolean {
  // Check file size
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    throw new Error('File too large')
  }
  
  // Check file type
  const allowedTypes = [
    'application/pdf',
    'text/plain',
    'application/rtf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]
  
  if (!allowedTypes.includes(file.type)) {
    throw new Error('File type not allowed')
  }
  
  // Check file name for malicious content
  const fileName = file.name.toLowerCase()
  if (fileName.includes('..') || fileName.includes('/') || fileName.includes('\\')) {
    throw new Error('Invalid file name')
  }
  
  return true
}

// Secure file path generation
function generateSecureFilePath(userId: string, threadId: string, fileName: string): string {
  const sanitizedFileName = fileName.replace(/[^a-zA-Z0-9.-]/g, '_')
  const timestamp = Date.now()
  const fileId = crypto.randomUUID()
  
  return `${userId}/${threadId}/${timestamp}_${fileId}_${sanitizedFileName}`
}
```

### Storage Bucket Policies

```sql
-- Secure storage policies
CREATE POLICY "Users can upload own documents" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'documents' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can view own documents" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'documents' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can update own documents" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'documents' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete own documents" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'documents' AND 
        auth.uid()::text = (storage.foldername(name))[1]
    );
```

### File Access Control

```javascript
// Secure file download
async function secureFileDownload(filePath: string, userId: string) {
  // Verify user owns the file
  const pathParts = filePath.split('/')
  const fileUserId = pathParts[0]
  
  if (fileUserId !== userId) {
    throw new Error('Access denied')
  }
  
  // Download file
  const { data, error } = await supabase.storage
    .from('documents')
    .download(filePath)
  
  if (error) {
    throw new Error('File not found')
  }
  
  return data
}
```

---

## Edge Function Security

### Environment Variable Security

```bash
# Secure environment variable management
# Never expose secrets in client-side code
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
# Service role key only in Edge Functions
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
```

### Function Input Validation

```typescript
// Comprehensive input validation in Edge Functions
interface VectorizeRequest {
  documentId: string
  userId: string
  content: string
  fileName: string
  fileType: string
}

function validateVectorizeRequest(request: any): VectorizeRequest {
  if (!request.documentId || typeof request.documentId !== 'string') {
    throw new Error('Invalid documentId')
  }
  
  if (!request.userId || typeof request.userId !== 'string') {
    throw new Error('Invalid userId')
  }
  
  if (!request.content || typeof request.content !== 'string') {
    throw new Error('Invalid content')
  }
  
  if (request.content.length > 10 * 1024 * 1024) { // 10MB limit
    throw new Error('Content too large')
  }
  
  return request as VectorizeRequest
}

// Use in Edge Function
serve(async (req) => {
  try {
    const request = await req.json()
    const validatedRequest = validateVectorizeRequest(request)
    
    // Process validated request
    const result = await vectorizeDocument(validatedRequest)
    
    return new Response(JSON.stringify(result), {
      headers: { 'Content-Type': 'application/json' }
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    })
  }
})
```

### Error Handling Security

```typescript
// Secure error handling - don't expose sensitive information
function handleError(error: any): string {
  // Log full error for debugging
  console.error('Full error:', error)
  
  // Return sanitized error message
  if (error.message.includes('API key')) {
    return 'Authentication error'
  }
  
  if (error.message.includes('database')) {
    return 'Database error'
  }
  
  if (error.message.includes('rate limit')) {
    return 'Rate limit exceeded'
  }
  
  return 'An error occurred'
}
```

---

## Multi-Tenant Architecture

### Tenant Isolation

The application implements **complete tenant isolation**:

```javascript
// Every operation is scoped to the user (tenant)
class TenantIsolation {
  static async getUserData(userId: string) {
    // All queries include user_id filter
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('user_id', userId)
    
    if (error) throw error
    return data
  }
  
  static async createUserResource(userId: string, resourceData: any) {
    // Always include user_id in new resources
    const { data, error } = await supabase
      .from('documents')
      .insert({
        ...resourceData,
        user_id: userId // Always set user_id
      })
      .select()
      .single()
    
    if (error) throw error
    return data
  }
}
```

### Cross-Tenant Security

```javascript
// Prevent cross-tenant data access
async function verifyTenantAccess(userId: string, resourceId: string, table: string) {
  const { data, error } = await supabase
    .from(table)
    .select('id, user_id')
    .eq('id', resourceId)
    .eq('user_id', userId) // Critical: verify user ownership
    .single()
  
  if (error || !data) {
    throw new Error('Access denied: Resource not found or access denied')
  }
  
  return data
}

// Use in all operations
async function updateDocument(userId: string, documentId: string, updates: any) {
  // Verify user owns the document
  await verifyTenantAccess(userId, documentId, 'documents')
  
  // Proceed with update
  const { data, error } = await supabase
    .from('documents')
    .update(updates)
    .eq('id', documentId)
    .eq('user_id', userId) // Double-check user ownership
    .select()
    .single()
  
  if (error) throw error
  return data
}
```

---

## Security Best Practices

### Code Security

```typescript
// Use TypeScript for type safety
interface SecureUser {
  id: string
  email: string
  user_metadata?: {
    full_name?: string
  }
}

// Validate all inputs
function sanitizeInput(input: string): string {
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove potential HTML tags
    .substring(0, 1000) // Limit length
}

// Use parameterized queries (handled by Supabase)
const { data } = await supabase
  .from('documents')
  .select('*')
  .eq('user_id', userId) // Safe parameterized query
```

### Dependency Security

```bash
# Regular security audits
npm audit

# Update dependencies regularly
npm update

# Use security-focused packages
npm install helmet
npm install express-rate-limit
npm install cors
```

### Environment Security

```bash
# Use different environments
# Development
VITE_APP_ENV=development
VITE_DEBUG=true

# Production
VITE_APP_ENV=production
VITE_DEBUG=false

# Never commit secrets
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "secrets/" >> .gitignore
```

### Monitoring & Alerting

```javascript
// Security monitoring
const securityMonitor = {
  failedLogins: new Map(),
  suspiciousActivity: new Map(),
  
  trackFailedLogin: (userId: string) => {
    const attempts = securityMonitor.failedLogins.get(userId) || 0
    securityMonitor.failedLogins.set(userId, attempts + 1)
    
    if (attempts > 5) {
      // Alert on suspicious activity
      securityMonitor.alertSuspiciousActivity(userId, 'Multiple failed logins')
    }
  },
  
  alertSuspiciousActivity: (userId: string, activity: string) => {
    console.warn(`Suspicious activity detected: ${activity} for user ${userId}`)
    // Send alert to security team
  }
}
```

---

## Compliance

### GDPR Compliance

```javascript
// GDPR data subject rights
class GDPRCompliance {
  // Right to access
  static async getUserData(userId: string) {
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('user_id', userId)
      .single()
    
    if (error) throw error
    return data
  }
  
  // Right to deletion
  static async deleteUserData(userId: string) {
    // Cascade deletion handled by foreign key constraints
    const { error } = await supabase.auth.admin.deleteUser(userId)
    
    if (error) throw error
    return { success: true }
  }
  
  // Right to portability
  static async exportUserData(userId: string) {
    const userData = {
      profile: await this.getUserData(userId),
      documents: await this.getUserDocuments(userId),
      threads: await this.getUserThreads(userId),
      conversations: await this.getUserConversations(userId)
    }
    
    return userData
  }
}
```

### Data Processing Records

```sql
-- Maintain data processing records
CREATE TABLE data_processing_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  operation_type TEXT NOT NULL,
  data_type TEXT NOT NULL,
  processing_purpose TEXT NOT NULL,
  legal_basis TEXT NOT NULL,
  processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  retention_period INTERVAL,
  metadata JSONB DEFAULT '{}'
);

-- Log data processing activities
INSERT INTO data_processing_logs (
  user_id,
  operation_type,
  data_type,
  processing_purpose,
  legal_basis,
  retention_period
) VALUES (
  'user-uuid',
  'document_upload',
  'document_content',
  'RAG processing for user queries',
  'legitimate_interest',
  INTERVAL '2 years'
);
```

### Privacy Policy Integration

```javascript
// Privacy policy consent tracking
class PrivacyConsent {
  static async trackConsent(userId: string, consentType: string, granted: boolean) {
    const { error } = await supabase
      .from('privacy_consents')
      .insert({
        user_id: userId,
        consent_type: consentType,
        granted: granted,
        granted_at: granted ? new Date().toISOString() : null,
        ip_address: 'tracked_ip', // Anonymized
        user_agent: 'tracked_user_agent' // Anonymized
      })
    
    if (error) throw error
  }
  
  static async checkConsent(userId: string, consentType: string): Promise<boolean> {
    const { data, error } = await supabase
      .from('privacy_consents')
      .select('granted')
      .eq('user_id', userId)
      .eq('consent_type', consentType)
      .order('created_at', { ascending: false })
      .limit(1)
      .single()
    
    if (error || !data) return false
    return data.granted
  }
}
```

---

## Security Checklist

### Pre-Deployment Security Checklist

- [ ] All tables have RLS enabled
- [ ] All RLS policies are properly configured
- [ ] Environment variables are secure
- [ ] API keys are properly managed
- [ ] Input validation is implemented
- [ ] Rate limiting is configured
- [ ] CORS is properly configured
- [ ] Error messages don't expose sensitive information
- [ ] Dependencies are up to date
- [ ] Security headers are configured

### Runtime Security Checklist

- [ ] Monitor failed login attempts
- [ ] Track suspicious activity
- [ ] Monitor API usage patterns
- [ ] Check for unauthorized access attempts
- [ ] Monitor database query performance
- [ ] Track storage access patterns
- [ ] Monitor Edge Function execution
- [ ] Check for data leakage

### Compliance Checklist

- [ ] GDPR compliance implemented
- [ ] Data processing records maintained
- [ ] Privacy policy integrated
- [ ] Consent tracking implemented
- [ ] Data retention policies configured
- [ ] Data export functionality available
- [ ] Data deletion functionality available
- [ ] Privacy impact assessment completed

---

## Security Resources

### Documentation

- [Supabase Security Documentation](https://supabase.com/docs/guides/security)
- [OpenAI Security Best Practices](https://platform.openai.com/docs/security)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)

### Tools

- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [Snyk Security Scanner](https://snyk.io/)
- [OWASP ZAP](https://owasp.org/www-project-zap/)

### Monitoring

- [Supabase Dashboard](https://app.supabase.com)
- [OpenAI Usage Dashboard](https://platform.openai.com/usage)
- [Application Performance Monitoring](https://supabase.com/docs/guides/observability) 