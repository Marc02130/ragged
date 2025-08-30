# Deno Configuration for Supabase Edge Functions

## Overview

This document explains how to use `deno.json` configuration files to manage imports and dependencies in Supabase Edge Functions, resolving TypeScript linter errors and providing better development experience.

## Problem Solved

The original Edge Functions used direct URL imports which caused TypeScript linter errors:
```typescript
// ❌ Causes linter errors
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
```

## Solution: deno.json Import Maps

Each Edge Function now has a `deno.json` file that defines import maps:

```json
{
  "imports": {
    "@supabase/supabase-js": "https://esm.sh/@supabase/supabase-js@2",
    "langchain/text_splitter": "https://esm.sh/langchain@0.1.0/text_splitter",
    "langchain/embeddings/openai": "https://esm.sh/langchain@0.1.0/embeddings/openai",
    "std/http/server": "https://deno.land/std@0.208.0/http/server.ts"
  }
}
```

This allows clean imports:
```typescript
// ✅ Clean, linter-friendly imports
import { serve } from "std/http/server"
import { createClient } from '@supabase/supabase-js'
```

## File Structure

```
supabase/functions/
├── vectorize/
│   ├── deno.json          # Import map for vectorization
│   └── index.ts
├── rag-query/
│   ├── deno.json          # Import map for RAG queries
│   └── index.ts
└── delete-thread/
    ├── deno.json          # Import map for thread deletion
    └── index.ts
```

## Configuration Details

### 1. Import Maps
Each `deno.json` defines import maps that map clean import names to actual URLs:

```json
{
  "imports": {
    "@supabase/supabase-js": "https://esm.sh/@supabase/supabase-js@2",
    "langchain/": "https://esm.sh/langchain@0.1.0/",
    "std/": "https://deno.land/std@0.208.0/"
  }
}
```

### 2. Compiler Options
TypeScript compiler options for Edge Functions:

```json
{
  "compilerOptions": {
    "allowJs": true,
    "lib": ["deno.window"],
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### 3. Lint Configuration
Deno linting rules:

```json
{
  "lint": {
    "rules": {
      "tags": ["recommended"]
    },
    "include": ["**/*.ts"]
  }
}
```

### 4. Format Configuration
Code formatting options:

```json
{
  "fmt": {
    "files": {
      "include": ["**/*.ts"]
    },
    "options": {
      "useTabs": false,
      "lineWidth": 80,
      "indentWidth": 2,
      "semiColons": true,
      "singleQuote": true,
      "proseWrap": "preserve"
    }
  }
}
```

### 5. Tasks
Development and deployment tasks:

```json
{
  "tasks": {
    "dev": "deno run --allow-net --allow-env --watch index.ts",
    "start": "deno run --allow-net --allow-env index.ts",
    "test": "deno test --allow-net --allow-env",
    "lint": "deno lint",
    "fmt": "deno fmt"
  }
}
```

## Usage

### Development
```bash
# Navigate to function directory
cd supabase/functions/vectorize

# Run in development mode
deno task dev

# Or use Supabase CLI
supabase functions serve vectorize --env-file .env.local
```

### Linting and Formatting
```bash
# Lint code
deno task lint

# Format code
deno task fmt

# Both
deno task lint && deno task fmt
```

### Testing
```bash
# Run tests
deno task test

# Test with Supabase CLI
supabase functions serve --env-file .env.local
```

## Benefits

### 1. Linter Compatibility
- ✅ Resolves TypeScript linter errors
- ✅ Provides proper type checking
- ✅ Enables IDE autocomplete

### 2. Dependency Management
- ✅ Centralized version control
- ✅ Easy dependency updates
- ✅ Consistent versions across functions

### 3. Development Experience
- ✅ Clean, readable imports
- ✅ Better IDE support
- ✅ Faster development cycles

### 4. Performance
- ✅ Deno can cache and optimize imports
- ✅ Faster function startup
- ✅ Reduced bundle sizes

## Migration Guide

### Step 1: Create deno.json
Create a `deno.json` file in each function directory with appropriate imports.

### Step 2: Update Import Statements
Replace direct URL imports with import map references:

```typescript
// Before
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

// After
import { serve } from "std/http/server"
```

### Step 3: Test Functions
```bash
# Test locally
supabase functions serve --env-file .env.local

# Deploy
supabase functions deploy
```

### Step 4: Verify
- ✅ No linter errors
- ✅ Functions work correctly
- ✅ Imports resolve properly

## Troubleshooting

### Common Issues

1. **Import Resolution Errors**
   ```bash
   # Check deno.json syntax
   deno fmt deno.json
   
   # Verify import map
   deno check index.ts
   ```

2. **Type Errors**
   ```bash
   # Update TypeScript configuration
   # Ensure lib includes "deno.window"
   ```

3. **Function Deployment Issues**
   ```bash
   # Test locally first
   supabase functions serve --env-file .env.local
   
   # Check logs
   supabase functions logs
   ```

### Debug Mode
Enable detailed logging:
```bash
# Set debug environment variable
export DEBUG=true

# Run with verbose output
deno run --allow-net --allow-env --log-level=debug index.ts
```

## Best Practices

### 1. Version Pinning
Always pin specific versions in import maps:
```json
{
  "imports": {
    "@supabase/supabase-js": "https://esm.sh/@supabase/supabase-js@2.39.0"
  }
}
```

### 2. Consistent Configuration
Use consistent deno.json configuration across all functions:
- Same compiler options
- Same lint rules
- Same format settings

### 3. Documentation
Document dependency changes:
- Update version numbers
- Note breaking changes
- Test thoroughly

### 4. Testing
Always test after configuration changes:
```bash
# Local testing
deno task test

# Function testing
supabase functions serve --env-file .env.local
```

## Environment Variables

Ensure these environment variables are set:
```bash
# .env.local
SUPABASE_URL=your-project-url
SUPABASE_SERVICE_ROLE_KEY=your-service-key
OPENAI_API_KEY=your-openai-key
```

## Deployment

### Local Development
```bash
# Start local development
supabase start

# Serve functions locally
supabase functions serve --env-file .env.local
```

### Production Deployment
```bash
# Deploy all functions
supabase functions deploy

# Deploy specific function
supabase functions deploy vectorize
```

## Monitoring

### Function Logs
```bash
# View function logs
supabase functions logs

# Follow logs in real-time
supabase functions logs --follow
```

### Performance Monitoring
- Monitor function execution times
- Track memory usage
- Watch for errors

## Conclusion

Using `deno.json` configuration files for Supabase Edge Functions provides:
- ✅ Better development experience
- ✅ Resolved linter errors
- ✅ Centralized dependency management
- ✅ Improved performance
- ✅ Easier maintenance

This setup ensures your Edge Functions are production-ready with proper TypeScript support and clean, maintainable code. 