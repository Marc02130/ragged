export type User = {
  id: string;
  email: string;
  created_at: string;
};

export type Source = {
  chunk_id: string;
  document_id: string;
  file_name: string;
  content: string;
  similarity: number;
};

export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources: Source[];
};

export type CreateMessageResponse = {
  user_message: Message;
  assistant_message: Message;
};

export type Thread = {
  id: string;
  title: string;
  status: 'active' | 'archived';
  document_count: number;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
};

export type Document = {
  id: string;
  thread_id: string;
  file_name: string;
  file_size: number;
  file_type: string;
  title: string;
  status: 'processing' | 'ready' | 'failed';
  embedding_model: string | null;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};
