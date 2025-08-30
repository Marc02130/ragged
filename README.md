# RAG App: Document Q&A with AI

This is a Retrieval-Augmented Generation (RAG) application that allows you to upload documents and have AI-powered conversations to query their content. It's designed for individual users, like researchers or students, who need to chat with their personal documents.

---

### Features

* **Secure User Authentication:** Sign up or log in with your email and password, or use OAuth for easy access.
* **Thread Management:** Create and manage separate conversations for different topics or documents.
* **Document Uploads:** Securely upload documents (PDF, DOCX, DOC, TXT, RTF) up to 10MB per file on a per-thread basis. The app then processes and vectorizes the content to prepare it for querying.
* **AI-Powered Chat:** Ask questions and get answers from your documents using a chat interface. The application uses your chat history and uploaded documents to provide accurate, relevant responses. Chat history is automatically vectorized for better context recall.
* **Data Privacy:** All your documents and conversations are securely scoped to your user ID, ensuring your data remains private.

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

#### Installation
1.  Clone the repository:
    ```bash
    git clone [repository URL]
    ```
2.  Navigate to the project directory:
    ```bash
    cd [project folder]
    ```
3.  Install dependencies:
    ```bash
    npm install
    ```

#### Configuration
1.  Copy `env.example` to `.env` and configure your credentials:
    * `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
    * `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anon key
    * `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
    * `OPENAI_API_KEY` - Your OpenAI API key
    * `OPENAI_EMBEDDING_MODEL` - Set to `text-embedding-ada-002`
    * `OPENAI_COMPLETION_MODEL` - Set to `gpt-4` or `gpt-3.5-turbo`
2.  Deploy the necessary database tables and Edge Functions to your Supabase project. The required tables are `user_info`, `threads`, `documents`, `conversations`, and `vector_chunks`.
3.  Ensure Row Level Security (RLS) is enabled and properly configured on your Supabase tables to enforce data isolation by `user_id` and `thread_id`.

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
2.  **Create a New Thread:** Start a new conversation by creating a thread.
3.  **Upload Documents:** Within a thread, upload the documents you want to query. The system will automatically process them.
4.  **Start Chatting:** Once your documents are processed, you can begin asking questions in the chat interface. The AI will use your documents to generate responses.
5.  **Manage Threads:** You can view, switch between, and delete your threads. Deleting a thread will archive the conversation history for your reference while deleting the live chat data.

---

### Tech Stack

* **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
* **Backend:** Supabase Edge Functions (TypeScript)
* **Database:** Supabase Postgres with PGVector extension
* **Storage:** Supabase Storage
* **AI:** OpenAI API (GPT-4, text-embedding-ada-002)
* **Document Processing:** Langchain.js
* **Authentication:** Supabase Auth
