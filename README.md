# RAGged: Intelligent Document Q&A with AI

A modern Retrieval-Augmented Generation (RAG) application that provides seamless document upload, vectorization, intelligent chat queries, and comprehensive thread management with archival capabilities. Built for individual users, researchers, and students who need to chat with their personal documents.

## 🚀 Key Features

- **Multi-Thread Support**: Create and manage multiple conversation threads
- **Document Processing**: Upload and vectorize PDF, DOCX, TXT, and RTF files
- **Intelligent Chat**: Context-aware responses using RAG with source attribution
- **Thread Archival**: Complete conversation preservation with vectorized archives
- **Cross-Thread Search**: Search across multiple threads for relevant context
- **Real-time Interface**: Modern React UI with drag-and-drop file upload
- **Secure Authentication**: Supabase Auth with JWT-based security
- **Vector Search**: Efficient similarity search using pgvector

---

### Core Features

* **Secure User Authentication:** Sign up or log in with your email and password, with JWT-based session management.
* **Multi-Thread Management:** Create and manage separate conversations for different topics or documents with full CRUD operations.
* **Document Uploads:** Securely upload documents (PDF, DOCX, TXT, RTF) up to 10MB per file with drag-and-drop interface and progress tracking.
* **AI-Powered Chat:** Ask questions and get context-aware answers using RAG with source attribution and similarity scores.
* **Thread Archival:** Complete conversation preservation with vectorized archives for future reference.
* **Cross-Thread Search:** Intelligent search across multiple threads for comprehensive context retrieval.
* **Data Privacy:** All data is securely scoped to your user ID with Row Level Security (RLS).

---

### Technical Architecture

The application is built with a modular, API-first approach to ensure a scalable and maintainable design.

* **Frontend:** A React application built with Vite that communicates with the backend via RESTful APIs. It uses the Supabase JS client for all interactions, including authentication, database, and storage.
* **Backend:** Logic is handled by **Supabase Edge Functions**, written in TypeScript. These functions manage key processes like document vectorization, RAG queries, and thread deletion. The backend uses the **Langchain.js** library for document processing with recommended settings (1000 token chunks, 200 token overlap).
* **Database:** **Supabase Postgres** serves as the primary database, utilizing the **PGVector extension** to handle vector storage and similarity searches for the RAG functionality.
* **Storage:** **Supabase Storage** is used for securely storing uploaded documents, with file paths scoped to individual users and threads (`/users/{user_id}/threads/{thread_id}/`).

---

### Getting Started

#### Prerequisites
* Node.js and npm installed.
* A Supabase account and project configured with PGVector extension enabled.
* An OpenAI API key with access to GPT-4 and text-embedding-ada-002 models.

#### Quick Start
1.  Clone the repository:
    ```bash
    git clone [repository URL]
    cd ragged
    ```
2.  Copy environment template and configure:
    ```bash
    cp env.example .env
    # Edit .env with your credentials
    ```
3.  Install dependencies:
    ```bash
    npm install
    ```
4.  Deploy backend (requires Supabase CLI):
    ```bash
    ./scripts/deploy.sh
    ```
5.  Start development server:
    ```bash
    npm run dev
    ```

#### Configuration
1.  Configure your environment variables in `.env`:
    * `VITE_SUPABASE_URL` - Your Supabase project URL
    * `VITE_SUPABASE_ANON_KEY` - Your Supabase anon key
    * `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
    * `OPENAI_API_KEY` - Your OpenAI API key
2.  The deployment script automatically sets up:
    * Database migrations with proper schema
    * Edge Functions for vectorization, RAG queries, and thread management
    * Row Level Security (RLS) policies
    * Storage buckets and policies

#### Development
```bash
# Start the development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

### How to Use

1.  **Sign Up / Log In:** Access the application and create a new account or log in with your credentials.
2.  **Create a New Thread:** Start a new conversation by creating a thread with a descriptive title.
3.  **Upload Documents:** Within a thread, drag and drop or browse to upload documents (PDF, DOCX, TXT, RTF). The system automatically processes and vectorizes them.
4.  **Start Chatting:** Once documents are processed, ask questions in the chat interface. The AI provides context-aware responses with source attribution.
5.  **Manage Threads:** View, switch between, archive, and delete threads. Deletion archives conversation history for future reference.
6.  **Cross-Thread Search:** The AI can search across multiple threads for comprehensive context when answering questions.

---

### Tech Stack

* **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
* **Backend:** Supabase Edge Functions (TypeScript/Deno)
* **Database:** Supabase Postgres with PGVector extension
* **Storage:** Supabase Storage with user-scoped buckets
* **AI:** OpenAI API (GPT-4, text-embedding-ada-002)
* **Document Processing:** Langchain.js with optimized chunking
* **Authentication:** Supabase Auth with JWT tokens
* **Vector Search:** Efficient similarity search with pgvector

---

## 📚 Documentation

- [Integration Guide](INTEGRATION_GUIDE.md) - Complete integration documentation
- [API Reference](docs/API.md) - Edge Function API documentation
- [Database Schema](docs/DATABASE.md) - Database structure and relationships
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions

## 🔒 Security Features

- **Row Level Security**: All data is user-scoped
- **JWT Authentication**: Secure API access
- **File Validation**: Upload security and type checking
- **Rate Limiting**: API protection against abuse
- **Data Privacy**: Complete user data isolation

## 📊 Performance Optimizations

- **Efficient Vector Search**: Optimized similarity queries
- **Batch Processing**: Large document handling
- **Caching**: Intelligent response caching
- **Lazy Loading**: Frontend performance optimization
- **Connection Pooling**: Database performance
