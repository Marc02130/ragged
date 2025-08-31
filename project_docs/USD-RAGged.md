# User Story Document: Simple RAG App

## Introduction
This document outlines key user stories based on the PRD, formatted as: **As a [user], I want [feature] so that [benefit].** Each includes acceptance criteria and technical notes for alignment with the TDD.

## User Stories

### US-001: User Authentication
**As a** user,  
**I want** to sign up and log in securely,  
**So that** I can access my personal RAG app data.

**Acceptance Criteria:**
- Support email/password and OAuth.
- Redirect to dashboard on success.
- Error messages for invalid credentials.

**Technical Notes:**
- Use Supabase Auth; store preferences in `user_info`.

### US-002: Create Thread
**As a** user,  
**I want** to create a new conversation thread,  
**So that** I can organize queries by topic.

**Acceptance Criteria:**
- Enter title (required).
- Thread appears in list with creation date.
- Redirect to new thread chat.

**Technical Notes:**
- Insert into `threads` via Edge Function.

### US-003: Upload Document to Thread
**As a** user,  
**I want** to upload documents to a thread,  
**So that** I can query them via RAG.

**Acceptance Criteria:**
- Support PDF/TXT/DOCX.
- Show upload progress and status (pending/ready).
- List uploaded docs in thread UI.

**Technical Notes:**
- Store in scoped bucket; trigger vectorization Edge Function.

### US-004: Perform RAG Query
**As a** user,  
**I want** to ask questions in a thread,  
**So that** I get answers based on my documents and history.

**Acceptance Criteria:**
- Type query in chat interface.
- Response includes sources if applicable.
- Maintain conversation continuity.

**Technical Notes:**
- Embed query; search `vector_chunks`; augment with history from `conversations`; OpenAI generate.

### US-005: Vectorize Chat History
**As a** user,  
**I want** my chat history vectorized automatically,  
**So that** future queries recall previous context.

**Acceptance Criteria:**
- Happens periodically without user action.
- Improves response relevance over time.

**Technical Notes:**
- Edge Function chunks and embeds messages; store in `vector_chunks`.

### US-006: Delete Thread with Archival
**As a** user,  
**I want** to delete a thread but archive its content,  
**So that** I can clean up while preserving data.

**Acceptance Criteria:**
- Confirmation prompt with warning.
- Archive as TXT/vectorized for later reference.
- Thread removed from active list.

**Technical Notes:**
- Retrieve `conversations`; export/vectorize; soft-delete in `threads`.

### US-007: Error Recovery
**As a** user,  
**I want** graceful handling of failures,  
**So that** I can retry without data loss.

**Acceptance Criteria:**
- Clear messages for upload/query errors.
- Retry options where applicable.

**Technical Notes:**
- Implement in Edge Functions with logging.

## Prioritization
- Must-Have: US-001 to US-006.
- Nice-to-Have: US-007.

## Dependencies
- All stories depend on auth and DB setup.