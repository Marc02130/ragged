// User and Authentication Types
export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface UserInfo {
  user_id: string;
  preferences: Record<string, any>;
  metadata?: Record<string, any>;
}

// Thread Management Types
export interface Thread {
  id: string;
  user_id: string;
  title: string;
  status: 'active' | 'archived';
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  document_count: number;
}

// Document Types
export interface Document {
  id: string;
  thread_id: string;
  user_id: string;
  file_path: string;
  file_name: string;
  file_size: number;
  file_type: string;
  title: string;
  content?: string;
  vector_status: 'pending' | 'processing' | 'ready' | 'error';
  status: 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  chunk_count?: number;
}

// Chat Types
export interface Conversation {
  id: string;
  thread_id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  vectorized?: boolean;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Array<{
    chunk_id: string;
    content: string;
    similarity: number;
  }>;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  error?: string;
}

export interface RAGQueryResponse {
  response: string;
  sources: Array<{
    chunk_id: string;
    content: string;
    similarity: number;
  }>;
}

// File Upload Types
export interface FileUploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  error?: string;
}

// Form Types
export interface CreateThreadForm {
  title: string;
}

export interface UploadDocumentForm {
  files: File[];
  threadId: string;
}

// Error Types
export interface AppError {
  message: string;
  code?: string;
  details?: any;
} 