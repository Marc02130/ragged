import { createClient } from '@supabase/supabase-js';
import type { 
  User, 
  Thread, 
  Document, 
  Conversation, 
  RAGQueryResponse,
  ApiResponse 
} from '../types';

// Initialize Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Authentication functions
export const auth = {
  signUp: async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });
    return { data, error };
  },

  signIn: async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { data, error };
  },

  signOut: async () => {
    const { error } = await supabase.auth.signOut();
    return { error };
  },

  getCurrentUser: async () => {
    const { data: { user }, error } = await supabase.auth.getUser();
    return { user, error };
  },

  onAuthStateChange: (callback: (user: User | null) => void) => {
    return supabase.auth.onAuthStateChange((event, session) => {
      callback(session?.user || null);
    });
  },
};

// Thread management functions
export const threads = {
  create: async (title: string): Promise<ApiResponse<Thread>> => {
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return { data: null as any, error: 'Unauthorized' };
    }

    const { data, error } = await supabase
      .from('threads')
      .insert({
        user_id: user.id,
        title,
        status: 'active',
        document_count: 0,
      })
      .select()
      .single();

    return { data, error: error?.message };
  },

  list: async (): Promise<ApiResponse<Thread[]>> => {
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return { data: [], error: 'Unauthorized' };
    }

    const { data, error } = await supabase
      .from('threads')
      .select('*')
      .eq('user_id', user.id)
      .eq('status', 'active')
      .order('last_activity_at', { ascending: false });

    return { data: data || [], error: error?.message };
  },

  delete: async (threadId: string): Promise<ApiResponse<boolean>> => {
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return { data: false, error: 'Unauthorized' };
    }

    // Call Edge Function to handle deletion and archival
    const { data, error } = await supabase.functions.invoke('delete-thread', {
      body: { threadId },
    });

    if (error) {
      return { data: false, error: error.message };
    }

    return { data: true, error: undefined };
  },
};

// Document management functions
export const documents = {
  upload: async (files: File[], threadId: string): Promise<ApiResponse<Document[]>> => {
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return { data: [], error: 'Unauthorized' };
    }

    const uploadPromises = files.map(async (file) => {
      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        throw new Error(`File ${file.name} exceeds 10MB limit`);
      }

      // Validate file type
      const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/rtf'
      ];
      
      if (!allowedTypes.includes(file.type)) {
        throw new Error(`File type ${file.type} not supported`);
      }

      // Generate unique filename
      const timestamp = Date.now();
      const fileName = `${timestamp}_${file.name}`;
      const filePath = `/users/${user.id}/threads/${threadId}/${fileName}`;

      // Upload to Supabase Storage
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('documents')
        .upload(filePath, file);

      if (uploadError) {
        throw new Error(`Upload failed: ${uploadError.message}`);
      }

      // Create document record
      const { data: docData, error: docError } = await supabase
        .from('documents')
        .insert({
          thread_id: threadId,
          user_id: user.id,
          file_path: filePath,
          file_name: file.name,
          file_size: file.size,
          file_type: file.type,
          vector_status: 'pending',
        })
        .select()
        .single();

      if (docError) {
        throw new Error(`Document record creation failed: ${docError.message}`);
      }

      // Trigger vectorization via Edge Function
      await supabase.functions.invoke('vectorize-document', {
        body: {
          docId: docData.doc_id,
          userId: user.id,
          threadId,
        },
      });

      return docData;
    });

    try {
      const results = await Promise.all(uploadPromises);
      return { data: results, error: undefined };
    } catch (error) {
      return { data: [], error: (error as Error).message };
    }
  },

  list: async (threadId: string): Promise<ApiResponse<Document[]>> => {
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return { data: [], error: 'Unauthorized' };
    }

    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('user_id', user.id)
      .eq('thread_id', threadId)
      .order('uploaded_at', { ascending: false });

    return { data: data || [], error: error?.message };
  },
};

// Chat functions
export const chat = {
  sendMessage: async (threadId: string, message: string): Promise<ApiResponse<RAGQueryResponse>> => {
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return { data: null as any, error: 'Unauthorized' };
    }

    // Call RAG query Edge Function
    const { data, error } = await supabase.functions.invoke('rag-query', {
      body: {
        query: message,
        threadId,
        userId: user.id,
      },
    });

    if (error) {
      return { data: null as any, error: error.message };
    }

    return { data, error: undefined };
  },

  getHistory: async (threadId: string): Promise<ApiResponse<Conversation[]>> => {
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return { data: [], error: 'Unauthorized' };
    }

    const { data, error } = await supabase
      .from('conversations')
      .select('*')
      .eq('user_id', user.id)
      .eq('thread_id', threadId)
      .order('timestamp', { ascending: true });

    return { data: data || [], error: error?.message };
  },

  saveMessage: async (threadId: string, role: 'user' | 'assistant', content: string): Promise<ApiResponse<Conversation>> => {
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return { data: null as any, error: 'Unauthorized' };
    }

    const { data, error } = await supabase
      .from('conversations')
      .insert({
        thread_id: threadId,
        user_id: user.id,
        role,
        content,
        vectorized: false,
      })
      .select()
      .single();

    return { data, error: error?.message };
  },
}; 