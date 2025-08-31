# RAGged Deployment Guide

Complete deployment guide for the RAGged application, covering development setup, production deployment, and environment configuration.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Edge Functions Deployment](#edge-functions-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Scaling Considerations](#scaling-considerations)

---

## Prerequisites

### Required Accounts & Services

1. **Supabase Account**
   - Sign up at [supabase.com](https://supabase.com)
   - Pro plan recommended for production (vector operations, higher limits)

2. **OpenAI API Account**
   - Sign up at [platform.openai.com](https://platform.openai.com)
   - Add billing information
   - Generate API key with access to:
     - GPT-4 (for chat completions)
     - text-embedding-ada-002 (for embeddings)

3. **GitHub Account** (for version control and CI/CD)

### Required Software

```bash
# Node.js 18+ and npm
node --version  # Should be 18.0.0 or higher
npm --version   # Should be 8.0.0 or higher

# Supabase CLI
npm install -g supabase

# Git
git --version

# Optional: Docker (for local development)
docker --version
```

---

## Development Setup

### 1. Clone and Initialize

```bash
# Clone the repository
git clone https://github.com/your-username/ragged.git
cd ragged

# Install dependencies
npm install

# Copy environment template
cp env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file:

```bash
# Supabase Configuration
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Optional: Development overrides
VITE_APP_ENV=development
VITE_DEBUG=true
```

### 3. Set Up Supabase Project

```bash
# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Or create new project
supabase projects create ragged-dev
```

### 4. Deploy Database Schema

```bash
# Deploy migrations
supabase db push

# Or run migrations manually
supabase migration up

# Verify schema
supabase db diff
```

### 5. Deploy Edge Functions

```bash
# Deploy all functions
supabase functions deploy

# Or deploy individually
supabase functions deploy vectorize
supabase functions deploy rag-query
supabase functions deploy delete-thread
```

### 6. Set Up Storage

```bash
# Create storage bucket
supabase storage create documents

# Set bucket policies
supabase storage policy create documents "Users can upload own documents" --policy "INSERT" --definition "bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]"
supabase storage policy create documents "Users can view own documents" --policy "SELECT" --definition "bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]"
```

### 7. Start Development Server

```bash
# Start development server
npm run dev

# The application will be available at http://localhost:5173
```

---

## Production Deployment

### 1. Production Environment Setup

#### Create Production Supabase Project

```bash
# Create production project
supabase projects create ragged-prod

# Link to production project
supabase link --project-ref your-production-project-ref
```

#### Configure Production Environment

```bash
# Set production environment variables
supabase secrets set SUPABASE_URL=your_production_supabase_url
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_production_service_role_key
supabase secrets set OPENAI_API_KEY=your_openai_api_key

# Set additional production secrets
supabase secrets set NODE_ENV=production
supabase secrets set LOG_LEVEL=info
```

### 2. Database Production Setup

#### Enable Required Extensions

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS "vector";

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for secure functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

#### Deploy Production Schema

```bash
# Deploy all migrations
supabase db push

# Verify production schema
supabase db diff --schema public
```

#### Optimize for Production

```sql
-- Create optimized indexes for production
CREATE INDEX CONCURRENTLY ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 200);

CREATE INDEX CONCURRENTLY ON vector_chunks (user_id, document_id) 
INCLUDE (content, metadata);

CREATE INDEX CONCURRENTLY ON documents (user_id, thread_id, status);
CREATE INDEX CONCURRENTLY ON conversations (thread_id, user_id, created_at);
CREATE INDEX CONCURRENTLY ON threads (user_id, status, updated_at);

-- Analyze tables for query optimization
ANALYZE vector_chunks;
ANALYZE documents;
ANALYZE conversations;
ANALYZE threads;
```

### 3. Edge Functions Production Deployment

#### Configure Function Settings

Update `supabase/config.toml`:

```toml
[functions.vectorize]
timeout = 300
memory = 512

[functions.rag-query]
timeout = 120
memory = 512

[functions.delete-thread]
timeout = 180
memory = 512
```

#### Deploy Functions

```bash
# Deploy all functions to production
supabase functions deploy --project-ref your-production-project-ref

# Verify deployment
supabase functions list --project-ref your-production-project-ref
```

#### Set Production Secrets

```bash
# Set secrets for production functions
supabase secrets set --project-ref your-production-project-ref SUPABASE_URL=your_production_url
supabase secrets set --project-ref your-production-project-ref SUPABASE_SERVICE_ROLE_KEY=your_production_service_role_key
supabase secrets set --project-ref your-production-project-ref OPENAI_API_KEY=your_openai_api_key
```

### 4. Frontend Production Build

#### Build for Production

```bash
# Install production dependencies
npm ci --only=production

# Build for production
npm run build

# Preview production build
npm run preview
```

#### Deploy Frontend

Choose your preferred hosting platform:

**Vercel (Recommended)**:
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to Vercel
vercel --prod

# Set environment variables in Vercel dashboard
```

**Netlify**:
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy to Netlify
netlify deploy --prod --dir=dist

# Set environment variables in Netlify dashboard
```

**AWS S3 + CloudFront**:
```bash
# Build and sync to S3
npm run build
aws s3 sync dist/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

---

## Environment Configuration

### Environment Variables Reference

#### Required Variables

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key
```

#### Optional Variables

```bash
# Application Configuration
VITE_APP_ENV=production
VITE_APP_NAME=RAGged
VITE_APP_VERSION=1.0.0

# Debug Configuration
VITE_DEBUG=false
VITE_LOG_LEVEL=info

# Feature Flags
VITE_ENABLE_CROSS_THREAD_SEARCH=true
VITE_ENABLE_THREAD_ARCHIVAL=true
VITE_MAX_FILE_SIZE=10485760

# Performance Configuration
VITE_VECTOR_SEARCH_LIMIT=8
VITE_CHAT_HISTORY_LIMIT=50
VITE_DOCUMENT_CHUNK_SIZE=1000
```

### Environment-Specific Configurations

#### Development

```bash
# .env.development
VITE_APP_ENV=development
VITE_DEBUG=true
VITE_LOG_LEVEL=debug
VITE_ENABLE_MOCK_DATA=true
```

#### Staging

```bash
# .env.staging
VITE_APP_ENV=staging
VITE_DEBUG=false
VITE_LOG_LEVEL=info
VITE_ENABLE_MOCK_DATA=false
```

#### Production

```bash
# .env.production
VITE_APP_ENV=production
VITE_DEBUG=false
VITE_LOG_LEVEL=warn
VITE_ENABLE_MOCK_DATA=false
```

---

## Database Setup

### Initial Schema Deployment

```bash
# Deploy initial schema
supabase db push

# Verify tables created
supabase db diff --schema public
```

### Required Database Functions

```sql
-- Vector similarity search function
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

-- Cross-thread search function
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

### Database Maintenance

#### Regular Maintenance Tasks

```sql
-- Update table statistics
ANALYZE vector_chunks;
ANALYZE documents;
ANALYZE conversations;
ANALYZE threads;

-- Clean up old data (optional)
DELETE FROM vector_chunks 
WHERE created_at < NOW() - INTERVAL '90 days'
AND metadata->>'source_type' = 'chat_history';

-- Vacuum tables
VACUUM ANALYZE vector_chunks;
VACUUM ANALYZE documents;
```

#### Performance Monitoring

```sql
-- Monitor slow queries
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  rows
FROM pg_stat_statements 
WHERE query LIKE '%vector_chunks%'
ORDER BY mean_time DESC
LIMIT 10;

-- Monitor index usage
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'vector_chunks';
```

---

## Edge Functions Deployment

### Function Configuration

#### Vectorize Function

```typescript
// supabase/functions/vectorize/index.ts
import { serve } from "std/http/server"
import { createClient } from '@supabase/supabase-js'
import { OpenAIEmbeddings } from "@langchain/openai"
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters"

// Configuration
const CHUNK_SIZE = 1000
const CHUNK_OVERLAP = 200
const MAX_CHUNKS = 100
const BATCH_SIZE = 10

serve(async (req) => {
  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  }

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers })
  }

  try {
    const { documentId, userId, content, fileName, fileType } = await req.json()
    
    // Process document
    const result = await vectorizeDocument(documentId, userId, content, fileName, fileType)
    
    return new Response(JSON.stringify(result), {
      headers: { ...headers, 'Content-Type': 'application/json' },
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...headers, 'Content-Type': 'application/json' },
    })
  }
})
```

#### RAG Query Function

```typescript
// supabase/functions/rag-query/index.ts
import { serve } from "std/http/server"
import { createClient } from '@supabase/supabase-js'
import { OpenAI } from "@langchain/openai"
import { OpenAIEmbeddings } from "@langchain/openai"

// Configuration
const DEFAULT_MODEL = 'gpt-4'
const DEFAULT_TEMPERATURE = 0.7
const MAX_RESULTS = 8
const SIMILARITY_THRESHOLD = 0.7

serve(async (req) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  }

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers })
  }

  try {
    const { threadId, userId, query, maxResults, includeChatHistory } = await req.json()
    
    // Perform RAG query
    const result = await performRAGQuery(threadId, userId, query, maxResults, includeChatHistory)
    
    return new Response(JSON.stringify(result), {
      headers: { ...headers, 'Content-Type': 'application/json' },
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...headers, 'Content-Type': 'application/json' },
    })
  }
})
```

### Deployment Commands

```bash
# Deploy all functions
supabase functions deploy

# Deploy specific function
supabase functions deploy vectorize

# Deploy with debug logging
supabase functions deploy --debug

# Check function status
supabase functions list

# View function logs
supabase functions logs vectorize --follow
```

### Function Environment Variables

```bash
# Set function-specific environment variables
supabase secrets set SUPABASE_URL=your_supabase_url
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
supabase secrets set OPENAI_API_KEY=your_openai_api_key

# Set additional configuration
supabase secrets set CHUNK_SIZE=1000
supabase secrets set CHUNK_OVERLAP=200
supabase secrets set MAX_CHUNKS=100
```

---

## Frontend Deployment

### Build Configuration

#### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable in production
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          supabase: ['@supabase/supabase-js'],
          ui: ['@headlessui/react', '@heroicons/react']
        }
      }
    }
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version)
  }
})
```

#### Environment-Specific Builds

```bash
# Development build
npm run build:dev

# Staging build
npm run build:staging

# Production build
npm run build:prod
```

### Deployment Platforms

#### Vercel Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to Vercel
vercel --prod

# Set environment variables
vercel env add VITE_SUPABASE_URL
vercel env add VITE_SUPABASE_ANON_KEY
vercel env add OPENAI_API_KEY
```

#### Netlify Deployment

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy to Netlify
netlify deploy --prod --dir=dist

# Set environment variables in Netlify dashboard
# Site settings > Environment variables
```

#### AWS S3 + CloudFront

```bash
# Create S3 bucket
aws s3 mb s3://your-ragged-bucket

# Configure bucket for static website hosting
aws s3 website s3://your-ragged-bucket --index-document index.html --error-document index.html

# Build and sync
npm run build
aws s3 sync dist/ s3://your-ragged-bucket --delete

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json

# Invalidate cache after deployment
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

---

## Monitoring & Maintenance

### Health Checks

#### Application Health Check

```typescript
// Health check endpoint
app.get('/health', async (req, res) => {
  const checks = {
    database: await checkDatabaseConnection(),
    vectorSearch: await checkVectorSearch(),
    openai: await checkOpenAIAPI(),
    storage: await checkStorageAccess(),
    timestamp: new Date().toISOString()
  }
  
  const healthy = Object.values(checks).every(check => check.status === 'ok')
  const statusCode = healthy ? 200 : 503
  
  res.status(statusCode).json({
    status: healthy ? 'healthy' : 'unhealthy',
    checks,
    version: process.env.npm_package_version
  })
})
```

#### Database Health Check

```sql
-- Check database connectivity and extensions
SELECT 
  'database' as component,
  'ok' as status,
  version() as version,
  current_database() as database_name;

-- Check pgvector extension
SELECT 
  'pgvector' as component,
  CASE 
    WHEN extname = 'vector' THEN 'ok'
    ELSE 'missing'
  END as status
FROM pg_extension WHERE extname = 'vector';

-- Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Logging & Monitoring

#### Application Logging

```typescript
// Configure logging
const logger = {
  info: (message: string, data?: any) => {
    console.log(`[INFO] ${message}`, data ? JSON.stringify(data) : '')
  },
  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error ? JSON.stringify(error) : '')
  },
  warn: (message: string, data?: any) => {
    console.warn(`[WARN] ${message}`, data ? JSON.stringify(data) : '')
  }
}

// Use in Edge Functions
logger.info('Processing document', { documentId, userId, fileSize })
```

#### Performance Monitoring

```typescript
// Performance monitoring
const performanceMonitor = {
  start: (operation: string) => {
    const start = performance.now()
    return {
      end: () => {
        const duration = performance.now() - start
        logger.info(`${operation} completed`, { duration: `${duration.toFixed(2)}ms` })
        return duration
      }
    }
  }
}

// Use in operations
const monitor = performanceMonitor.start('vector_search')
const results = await performVectorSearch(query, userId)
monitor.end()
```

### Backup & Recovery

#### Database Backups

```bash
# Create database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql $DATABASE_URL < backup_20240101_120000.sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ragged_backup_$DATE.sql"

pg_dump $DATABASE_URL > $BACKUP_FILE
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "ragged_backup_*.sql.gz" -mtime +7 -delete
```

#### Storage Backups

```bash
# Backup storage bucket
aws s3 sync s3://your-bucket-name /backups/storage/

# Restore storage
aws s3 sync /backups/storage/ s3://your-bucket-name
```

---

## Scaling Considerations

### Database Scaling

#### Connection Pooling

```typescript
// Implement connection pooling
import { Pool } from 'pg'

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20, // Adjust based on your plan
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})

// Use in Edge Functions
async function withConnection(callback) {
  const client = await pool.connect()
  try {
    return await callback(client)
  } finally {
    client.release()
  }
}
```

#### Query Optimization

```sql
-- Optimize vector search queries
CREATE INDEX CONCURRENTLY ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 200);

-- Partition large tables
CREATE TABLE vector_chunks_partitioned (
  LIKE vector_chunks INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE vector_chunks_2024_01 PARTITION OF vector_chunks_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Application Scaling

#### Caching Strategy

```typescript
// Implement Redis caching
import { Redis } from 'ioredis'

const redis = new Redis(process.env.REDIS_URL)

// Cache frequently accessed data
async function getCachedData(key: string, fetchFn: () => Promise<any>) {
  const cached = await redis.get(key)
  if (cached) {
    return JSON.parse(cached)
  }
  
  const data = await fetchFn()
  await redis.setex(key, 3600, JSON.stringify(data)) // Cache for 1 hour
  return data
}
```

#### Load Balancing

```nginx
# Nginx configuration for load balancing
upstream ragged_backend {
    server backend1.example.com:3000;
    server backend2.example.com:3000;
    server backend3.example.com:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://ragged_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Cost Optimization

#### OpenAI API Optimization

```typescript
// Implement token usage tracking
const tokenTracker = {
  totalTokens: 0,
  totalCost: 0,
  
  trackUsage: (tokens: number, model: string) => {
    const costPerToken = getCostPerToken(model)
    tokenTracker.totalTokens += tokens
    tokenTracker.totalCost += tokens * costPerToken
    
    // Log usage
    logger.info('Token usage tracked', {
      tokens,
      model,
      totalTokens: tokenTracker.totalTokens,
      totalCost: tokenTracker.totalCost
    })
  }
}

// Use in API calls
const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: messages,
  max_tokens: 1000
})

tokenTracker.trackUsage(response.usage.total_tokens, 'gpt-4')
```

#### Database Cost Optimization

```sql
-- Monitor query performance
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  rows
FROM pg_stat_statements 
ORDER BY total_time DESC
LIMIT 10;

-- Optimize expensive queries
EXPLAIN ANALYZE SELECT * FROM vector_chunks 
WHERE user_id = 'user-uuid' 
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector 
LIMIT 5;
```

---

## Security Considerations

### Environment Security

```bash
# Use environment-specific secrets
# Development
supabase secrets set --env-file .env.development

# Production
supabase secrets set --env-file .env.production

# Rotate secrets regularly
supabase secrets set OPENAI_API_KEY=new_api_key
```

### Database Security

```sql
-- Enable RLS on all tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_chunks ENABLE ROW LEVEL SECURITY;

-- Create secure policies
CREATE POLICY "Users can only access own data" ON documents
    FOR ALL USING (auth.uid() = user_id);
```

### API Security

```typescript
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
```

---

## Troubleshooting Deployment

### Common Deployment Issues

#### Edge Function Deployment Fails

```bash
# Check function logs
supabase functions logs vectorize --follow

# Verify environment variables
supabase secrets list

# Test function locally
supabase functions serve vectorize --env-file .env.local
```

#### Database Migration Issues

```bash
# Check migration status
supabase migration list

# Reset database (development only)
supabase db reset

# Apply specific migration
supabase migration up --include-all
```

#### Frontend Build Issues

```bash
# Clear build cache
rm -rf node_modules/.vite
rm -rf dist

# Reinstall dependencies
npm ci

# Check for TypeScript errors
npm run type-check

# Build with verbose logging
npm run build -- --debug
```

### Performance Issues

#### Slow Vector Searches

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes 
WHERE tablename = 'vector_chunks';

-- Recreate optimized index
DROP INDEX IF EXISTS vector_chunks_embedding_idx;
CREATE INDEX CONCURRENTLY ON vector_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 200);
```

#### High Memory Usage

```bash
# Monitor Edge Function memory usage
supabase functions logs --follow | grep "memory"

# Reduce batch sizes in vectorization
supabase secrets set BATCH_SIZE=5
```

---

## Support & Resources

### Documentation

- [Supabase Documentation](https://supabase.com/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Vite Documentation](https://vitejs.dev/guide/)
- [React Documentation](https://react.dev/)

### Community Support

- [Supabase Discord](https://discord.supabase.com)
- [GitHub Issues](https://github.com/your-repo/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/supabase)

### Monitoring Tools

- [Supabase Dashboard](https://app.supabase.com)
- [OpenAI Usage Dashboard](https://platform.openai.com/usage)
- [Vercel Analytics](https://vercel.com/analytics)
- [Netlify Analytics](https://www.netlify.com/products/analytics/) 