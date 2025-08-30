```
# Example Prompts for Building a Simple RAG App (Updated)

## App Overview
A basic RAG app: Users authenticate via Supabase (auth.users for login). Custom tables: user_info (e.g., preferences), documents (per user/thread, stored in Supabase Storage with metadata/vectors in PGVector), threads/conversations (store thread IDs, chat history per user; history is saved, vectorized for RAG recall; users can have multiple threads/conversations). Documents are scoped per user/thread. Users can delete OpenAI threads (with confirmation warning to verify they want to delete; upon deletion, retrieve conversation, vectorize it, and save as TXT document in Storage with vectors in PGVector), but app archives documents/conversations in Supabase (e.g., mark as archived in threads table) for future reference. Backend uses Supabase Edge Functions (TypeScript/Deno) exclusively. Chat history is vectorized/stored in Supabase PGVector for "going back" via RAG queries.

## Full Prompt Set

### Prompt 1: Initial PRD Draft
- **Prompt Text**: "Draft a high-level PRD for a simple RAG app where users (who can have multiple threads/conversations) upload documents per thread and user for vectorization and chat-based interrogation. Include core features: Secure upload to Supabase Storage (scoped per user/thread), Langchain-based vectorization (split docs, embed with OpenAI, store vectors in Supabase PGVector), OpenAI-powered RAG queries, save/vectorize thread chat history in Supabase for conversation recall, and thread deletion (deletes OpenAI thread with confirmation warning to verify deletion; upon deletion, retrieve conversation, vectorize it, and save as TXT document in Storage with vectors in PGVector; archives docs/conversations in Supabase for reference). Tech stack: API-first React frontend, Supabase for auth/storage/DB (custom tables: user_info, documents, threads/conversations) with Edge Functions (TypeScript) for backend logic. Focus on modularity for extensions and basic privacy/compliance requirements."
- **Tool/Context**: Grok or Claude for structured planning.
- **Expected Output Notes**: A 2-3 page PRD with sections on objectives, features (including per-user/thread scoping, multiple threads per user, and archive on deletion), tech specs, and risks. Verify for completeness (e.g., add lab-specific compliance like data auditing if needed).
- **Relevance to Lab Work**: Mirrors drafting specs for LIMS integrations, e.g., Sapio webhook requirements.

- **Iteration 1**: "Expand the PRD user stories: Add details for upload flow (e.g., file size limits, associating docs to specific threads/users with support for multiple threads) and query handling (e.g., maintaining/vectorizing chat history in Supabase threads table)."
- **Iteration 2**: "Refine the PRD for scalability: Suggest Supabase Edge Functions for vector queries, RLS on custom tables (user_info, documents, threads), and confirmation warning UI for thread deletion (retrieve/vectorize/save conversation as TXT/vectors, while archiving in Supabase), with UI for managing multiple threads."

### Prompt 2: Detailed Requirements Refinement
- **Prompt Text**: "Refine requirements for the RAG app PRD: Specify Langchain vectorization steps (split docs, embed with OpenAI, use FAISS index in Supabase PGVector; store per user/thread). Detail Supabase setup (PGVector for vectors, auth with JWT, custom tables: user_info for preferences, documents for metadata/vectors, threads/conversations for IDs/history with support for multiple threads per user; save/vectorize chat history). Include API endpoints like /upload (associate to thread), /query, and /delete-thread (deletes OpenAI thread with confirmation warning to verify deletion; upon deletion, retrieve conversation, vectorize it, and save as TXT document in Storage with vectors in PGVector; archives docs/history in Supabase threads table). Ensure documents/chat history are user-scoped via RLS."
- **Tool/Context**: Claude for iterative refinement.
- **Expected Output Notes**: Bullet-point requirements doc with diagrams (e.g., data flow). Check for edge cases like multi-thread access per user or archive retrieval.
- **Relevance to Lab Work**: Like detailing DB schemas for lab data pushes in Sapio-MGL integrations.

- **Iteration 1**: "Add security requirements: Ensure uploads use Supabase storage buckets with RLS, tie documents/threads to user IDs (supporting multiple threads per user), and vectorize saved chat history for RAG-enabled recall."
- **Iteration 2**: "Incorporate testing requirements: Unit tests for vectorization (per thread), integration tests for thread deletion (OpenAI delete + retrieve/vectorize/save as TXT/vectors + Supabase archive) and multiple thread management."

### Prompt 3: Frontend Boilerplate Generation
- **Prompt Text**: "Generate React code for the RAG app frontend: API-first structure with components for user auth (Supabase), document upload form (scoped to current thread), chat interface for RAG queries (displaying vectorized history), thread list/manager (for multiple threads per user), and a delete thread button with confirmation warning modal to verify deletion (deletes OpenAI thread, retrieves/vectorizes/saves conversation as TXT/vectors, but archives in Supabase). Use hooks for state (e.g., useState for chat history/threads) and integrate Supabase client for calling Edge Functions and querying custom tables (user_info, documents, threads)."
- **Tool/Context**: Cursor for code generation.
- **Expected Output Notes**: Folder structure with App.js, UploadComponent.js, ChatComponent.js, ThreadManager.js. Review for React best practices and manual tweaks for lab UI (e.g., simple dashboards).
- **Relevance to Lab Work**: Useful for quick prototypes of LIMS UIs, like Sapio plugin interfaces.

- **Iteration 1**: "Add error handling to the frontend: Display messages for upload failures, query errors, or thread deletion confirmations from Supabase Edge Functions (confirm deletion and handle retrieve/vectorize/save as TXT/vectors + Supabase archive)."
- **Iteration 2**: "Integrate loading states: Spinners for vectorization of uploads/history and chat responses; list and switch between multiple user threads from Supabase threads table, with archive access option."

### Prompt 4: Backend Vectorization Logic (Supabase Edge)
- **Prompt Text**: "Write TypeScript code for a Supabase Edge Function to handle RAG app vectorization: Use Langchain.js to process uploaded docs (split with RecursiveCharacterTextSplitter, embed via OpenAI, create FAISS index; store vectors/metadata in Supabase PGVector/documents table per user/thread). Also vectorize/save chat history to threads table/PGVector for recall (supporting multiple threads per user)."
- **Tool/Context**: Cursor or Grok for backend scripts.
- **Expected Output Notes**: index.ts with Langchain imports and functions like vectorize_doc() and vectorize_history(). Test locally for embedding accuracy.
- **Relevance to Lab Work**: Parallels scripting data ingestion in lab DBs, e.g., tracer plate associations.

- **Iteration 1**: "Optimize for large docs: Add chunking limits and batch insertion to Supabase PGVector; enforce per-user/thread scoping via RLS (handling multiple threads)."
- **Iteration 2**: "Include logging: Use console.log to track vectorization steps for debugging in Edge Functions; handle chat history vectorization separately."

### Prompt 5: RAG Query Integration (Supabase Edge)
- **Prompt Text**: "Implement RAG query logic in TypeScript for a Supabase Edge Function: Use OpenAI API to query the Supabase vector store (via similarity search on documents/threads tables), combine with user prompt for contextual responses (including vectorized chat history recall). Handle chat history saving/vectorization per thread/user (supporting multiple threads)."
- **Tool/Context**: Grok for AI-specific code.
- **Expected Output Notes**: query.ts with functions like rag_query(prompt, vector_store). Verify responses for relevance, including history integration.
- **Relevance to Lab Work**: Like querying lab databases for sample data in LIMS workflows.

- **Iteration 1**: "Add retrieval filtering: Limit to top-k similar chunks from user/thread-specific vectors in documents/threads tables (across multiple threads)."
- **Iteration 2**: "Handle no-results: Return a fallback message if no relevant vectors are found; append new messages to threads table and vectorize."

### Prompt 6: Full System Integration
- **Prompt Text**: "Integrate the RAG app: Combine frontend React with Supabase Edge Functions (TypeScript) for APIs. Ensure seamless flow from upload (to documents table per thread) to vectorization to chat queries with OpenAI RAG (saving/vectorizing history in threads table; support multiple threads per user). Include thread deletion logic (deletes OpenAI thread with confirmation warning to verify deletion; upon deletion, retrieve conversation, vectorize it, save as TXT document in Storage with vectors in PGVector; archives docs/history in Supabase threads table for reference)."
- **Tool/Context**: Cursor for end-to-end assembly.
- **Expected Output Notes**: Deployment guide with supabase/functions setup. Run e2e tests.
- **Relevance to Lab Work**: Simulates integrating modular components in LIMS, like Sapio extensions.

- **Iteration 1**: "Add auth checks: Ensure all Edge Functions require Supabase JWT validation and query user_info for preferences."
- **Iteration 2**: "Include deployment instructions for Supabase CLI to push Edge Functions and set up custom tables with RLS; detail deletion flow (retrieve/vectorize/save as TXT/vectors + archive) and multiple thread handling."

### Prompt 7: Testing and Debugging
- **Prompt Text**: "Generate test suite for the RAG app: Unit tests for Langchain vectorization in Edge Functions (per thread), integration tests for Supabase storage/retrieval (documents/threads tables), e2e tests for chat queries with OpenAI (including history vectorization and multiple threads per user), and thread deletion (OpenAI delete + retrieve/vectorize/save as TXT/vectors + Supabase archive with confirmation warning to verify deletion)."
- **Tool/Context**: Cursor for test code.
- **Expected Output Notes**: tests/ folder with Deno test scripts. Focus on coverage for compliance-sensitive parts.
- **Relevance to Lab Work**: Essential for validating LIMS code, e.g., Sapio bug fixes.

- **Iteration 1**: "Add mock data: Use fake docs and history entries for offline testing in Edge Functions, scoped to mock users with multiple threads."
- **Iteration 2**: "Include performance tests: Measure query latency for RAG responses via Edge, including history recall and archive access across multiple threads."

### Prompt 8: Documentation Generation
- **Prompt Text**: "Create user/developer docs for the RAG app: README with setup instructions (including Supabase Edge deployment and custom tables: user_info, documents, threads/conversations with support for multiple threads per user), API docs for Edge Functions, troubleshooting for common issues like vector DB errors or thread deletion warnings (confirmation to verify deletion; includes retrieve/vectorize/save as TXT/vectors), and notes on per-user/thread scoping."
- **Tool/Context**: Grok for markdown docs.
- **Expected Output Notes**: README.md with sections on installation, usage, and FAQs. Customize for lab users.
- **Relevance to Lab Work**: Like documenting LIMS integrations for team handoff.

- **Iteration 1**: "Add diagrams: Include a data flow diagram for upload-to-query process via Edge Functions, showing table interactions (documents/threads) and deletion flow (retrieve/vectorize/save as TXT/vectors + archive) for multiple threads."
- **Iteration 2**: "Incorporate best practices: Tips for scaling vector storage in Supabase PGVector for lab-scale data, and RLS setup for user/thread privacy with archive retention and multiple thread support."

## How to Use These Prompts
- Iterate based on outputs; always verify code for security/compliance in lab environments.
- Inspired by fundflowai repo on GitHub.
- Created by Marc Breneiser, August 2025.
```