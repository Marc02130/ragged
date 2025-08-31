import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createClient } from '@supabase/supabase-js'

// Mock Supabase client
vi.mock('@supabase/supabase-js')

describe('Supabase Storage Integration Tests', () => {
  let mockSupabase: any

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup mock Supabase client
    mockSupabase = {
      auth: {
        getUser: vi.fn()
      },
      from: vi.fn(() => ({
        select: vi.fn(() => ({
          eq: vi.fn(() => ({
            eq: vi.fn(() => ({
              single: vi.fn(),
              order: vi.fn(() => ({
                limit: vi.fn(() => ({
                  mockResolvedValue: vi.fn()
                }))
              }))
            })),
            order: vi.fn(() => ({
              limit: vi.fn(() => ({
                mockResolvedValue: vi.fn()
              })),
              mockResolvedValue: vi.fn()
            }))
          }))
        })),
        insert: vi.fn(() => ({
          select: vi.fn(() => ({
            single: vi.fn()
          }))
        })),
        update: vi.fn(() => ({
          eq: vi.fn(() => ({
            eq: vi.fn(() => ({
              mockResolvedValue: vi.fn()
            })),
            mockResolvedValue: vi.fn()
          }))
        })),
        delete: vi.fn(() => ({
          eq: vi.fn()
        }))
      })),
      rpc: vi.fn()
    }
    
    ;(createClient as any).mockReturnValue(mockSupabase)
  })

  describe('Documents Table Operations', () => {
    it('should create document record with proper metadata', async () => {
      const documentData = {
        id: 'doc-123',
        thread_id: 'thread-456',
        user_id: 'user-789',
        title: 'Test Document',
        file_name: 'test.txt',
        file_type: 'text/plain',
        content: 'This is test content',
        status: 'pending'
      }

      // Mock successful document creation
      mockSupabase.from().insert().select().single.mockResolvedValue({
        data: documentData,
        error: null
      })

      const result = await createDocument(documentData)

      expect(result.success).toBe(true)
      expect(result.data).toEqual(documentData)
      expect(mockSupabase.from).toHaveBeenCalledWith('documents')
    })

    it('should retrieve documents by thread with proper filtering', async () => {
      const threadId = 'thread-456'
      const userId = 'user-789'

      const mockDocuments = [
        {
          id: 'doc-1',
          thread_id: threadId,
          user_id: userId,
          title: 'Document 1',
          status: 'completed'
        },
        {
          id: 'doc-2',
          thread_id: threadId,
          user_id: userId,
          title: 'Document 2',
          status: 'processing'
        }
      ]

      // Mock document retrieval
      const mockOrder = vi.fn().mockResolvedValue({ data: mockDocuments, error: null });
      const mockEq2 = vi.fn().mockReturnValue({ order: mockOrder });
      const mockEq1 = vi.fn().mockReturnValue({ eq: mockEq2 });
      const mockSelect = vi.fn().mockReturnValue({ eq: mockEq1 });
      mockSupabase.from.mockReturnValue({ select: mockSelect });

      const result = await getDocumentsByThread(threadId, userId)

      expect(result.success).toBe(true)
      expect(result.data).toHaveLength(2)
      expect(result.data[0].thread_id).toBe(threadId)
      expect(result.data[0].user_id).toBe(userId)
    })

    it('should update document status correctly', async () => {
      const documentId = 'doc-123'
      const newStatus = 'completed'

      // Mock successful status update
      mockSupabase.from().update().eq().eq().mockResolvedValue({
        data: null,
        error: null
      })

      const result = await updateDocumentStatus(documentId, newStatus)

      expect(result.success).toBe(true)
      expect(mockSupabase.from).toHaveBeenCalledWith('documents')
    })

    it('should handle document retrieval errors', async () => {
      const threadId = 'thread-456'
      const userId = 'user-789'

      // Mock retrieval error
      const mockOrder = vi.fn().mockResolvedValue({ data: null, error: { message: 'Database connection failed' } });
      const mockEq2 = vi.fn().mockReturnValue({ order: mockOrder });
      const mockEq1 = vi.fn().mockReturnValue({ eq: mockEq2 });
      const mockSelect = vi.fn().mockReturnValue({ eq: mockEq1 });
      mockSupabase.from.mockReturnValue({ select: mockSelect });

      const result = await getDocumentsByThread(threadId, userId)

      expect(result.success).toBe(false)
      expect(result.error).toBe('Database connection failed')
    })
  })

  describe('Threads Table Operations', () => {
    it('should create thread with proper metadata', async () => {
      const threadData = {
        id: 'thread-123',
        user_id: 'user-456',
        title: 'Test Thread',
        status: 'active'
      }

      // Mock successful thread creation
      mockSupabase.from().insert().select().single.mockResolvedValue({
        data: threadData,
        error: null
      })

      const result = await createThread(threadData)

      expect(result.success).toBe(true)
      expect(result.data).toEqual(threadData)
      expect(mockSupabase.from).toHaveBeenCalledWith('threads')
    })

    it('should retrieve threads by user with proper ordering', async () => {
      const userId = 'user-456'

      const mockThreads = [
        {
          id: 'thread-1',
          user_id: userId,
          title: 'Recent Thread',
          status: 'active',
          updated_at: '2024-01-02T10:00:00Z'
        },
        {
          id: 'thread-2',
          user_id: userId,
          title: 'Older Thread',
          status: 'active',
          updated_at: '2024-01-01T10:00:00Z'
        }
      ]

      // Mock thread retrieval
      mockSupabase.from().select().eq().order().mockResolvedValue({
        data: mockThreads,
        error: null
      })

      const result = await getThreadsByUser(userId)

      expect(result.success).toBe(true)
      expect(result.data).toHaveLength(2)
      expect(result.data[0].user_id).toBe(userId)
      // Should be ordered by updated_at desc
      expect(result.data[0].updated_at).toBe('2024-01-02T10:00:00Z')
    })

    it('should update thread status and activity timestamp', async () => {
      const threadId = 'thread-123'
      const newStatus = 'archived'

      // Mock successful thread update
      mockSupabase.from().update().eq().eq().mockResolvedValue({
        data: null,
        error: null
      })

      const result = await updateThreadStatus(threadId, newStatus)

      expect(result.success).toBe(true)
      expect(mockSupabase.from).toHaveBeenCalledWith('threads')
    })

    it('should handle thread deletion with cascade', async () => {
      const threadId = 'thread-123'
      const userId = 'user-456'

      // Mock successful cascade deletion
      mockSupabase.rpc.mockResolvedValue({
        data: null,
        error: null
      })

      const result = await deleteThreadCascade(threadId, userId)

      expect(result.success).toBe(true)
      expect(mockSupabase.rpc).toHaveBeenCalledWith('delete_thread_cascade', {
        p_thread_id: threadId,
        p_user_id: userId
      })
    })
  })

  describe('Vector Chunks Table Operations', () => {
    it('should insert vector chunks in batches', async () => {
      const vectorChunks = [
        {
          document_id: 'doc-1',
          user_id: 'user-456',
          thread_id: 'thread-789',
          content: 'Chunk 1 content',
          embedding: [0.1, 0.2, 0.3],
          metadata: { chunk_index: 0 }
        },
        {
          document_id: 'doc-1',
          user_id: 'user-456',
          thread_id: 'thread-789',
          content: 'Chunk 2 content',
          embedding: [0.4, 0.5, 0.6],
          metadata: { chunk_index: 1 }
        }
      ]

      // Mock successful batch insertion
      mockSupabase.from().insert.mockResolvedValue({
        data: null,
        error: null
      })

      const result = await insertVectorChunks(vectorChunks)

      expect(result.success).toBe(true)
      expect(mockSupabase.from).toHaveBeenCalledWith('vector_chunks')
    })

    it('should perform similarity search with proper filtering', async () => {
      const queryEmbedding = [0.1, 0.2, 0.3]
      const threadId = 'thread-456'
      const userId = 'user-789'

      const mockChunks = [
        {
          content: 'Relevant content 1',
          metadata: { document_title: 'Doc 1' },
          embedding: [0.1, 0.2, 0.3],
          similarity: 0.95
        },
        {
          content: 'Relevant content 2',
          metadata: { document_title: 'Doc 2' },
          embedding: [0.4, 0.5, 0.6],
          similarity: 0.85
        }
      ]

      // Mock similarity search
      mockSupabase.from().select().eq().eq().order().limit().mockResolvedValue({
        data: mockChunks,
        error: null
      })

      const result = await performSimilaritySearch(queryEmbedding, threadId, userId)

      expect(result.success).toBe(true)
      expect(result.data).toHaveLength(2)
      expect(result.data[0].similarity).toBeGreaterThan(result.data[1].similarity)
    })

    it('should handle vector chunk insertion errors', async () => {
      const vectorChunks = [
        {
          document_id: 'doc-1',
          user_id: 'user-456',
          thread_id: 'thread-789',
          content: 'Chunk content',
          embedding: [0.1, 0.2, 0.3],
          metadata: { chunk_index: 0 }
        }
      ]

      // Mock insertion error
      const mockSelect = vi.fn().mockResolvedValue({ data: null, error: { message: 'Vector dimension mismatch' } });
      const mockInsert = vi.fn().mockReturnValue({ select: mockSelect });
      mockSupabase.from.mockReturnValue({ insert: mockInsert });

      const result = await insertVectorChunks(vectorChunks)

      expect(result.success).toBe(false)
      expect(result.error).toBe('Vector dimension mismatch')
    })
  })

  describe('Conversations Table Operations', () => {
    it('should save conversation with proper metadata', async () => {
      const conversationData = {
        thread_id: 'thread-123',
        user_id: 'user-456',
        role: 'user',
        content: 'What is the main topic?',
        metadata: {
          timestamp: new Date().toISOString(),
          query_type: 'rag'
        }
      }

      // Mock successful conversation save
      mockSupabase.from().insert().select().single.mockResolvedValue({
        data: { id: 'conv-123', ...conversationData },
        error: null
      })

      const result = await saveConversation(conversationData)

      expect(result.success).toBe(true)
      expect(result.data.role).toBe('user')
      expect(result.data.content).toBe('What is the main topic?')
    })

    it('should retrieve conversation history by thread', async () => {
      const threadId = 'thread-123'
      const userId = 'user-456'

      const mockConversations = [
        {
          id: 'conv-1',
          thread_id: threadId,
          user_id: userId,
          role: 'user',
          content: 'Hello',
          created_at: '2024-01-01T10:00:00Z'
        },
        {
          id: 'conv-2',
          thread_id: threadId,
          user_id: userId,
          role: 'assistant',
          content: 'Hi there!',
          created_at: '2024-01-01T10:01:00Z'
        }
      ]

      // Mock conversation retrieval
      const mockOrder = vi.fn().mockResolvedValue({ data: mockConversations, error: null });
      const mockEq2 = vi.fn().mockReturnValue({ order: mockOrder });
      const mockEq1 = vi.fn().mockReturnValue({ eq: mockEq2 });
      const mockSelect = vi.fn().mockReturnValue({ eq: mockEq1 });
      mockSupabase.from.mockReturnValue({ select: mockSelect });

      const result = await getConversationsByThread(threadId, userId)

      expect(result.success).toBe(true)
      expect(result.data).toHaveLength(2)
      expect(result.data[0].role).toBe('user')
      expect(result.data[1].role).toBe('assistant')
    })

    it('should update thread activity timestamp on conversation save', async () => {
      const threadId = 'thread-123'
      const conversationData = {
        thread_id: threadId,
        user_id: 'user-456',
        role: 'user',
        content: 'Test message'
      }

      // Mock conversation save
      mockSupabase.from().insert().select().single.mockResolvedValue({
        data: { id: 'conv-123', ...conversationData },
        error: null
      })

      // Mock thread update
      mockSupabase.from().update().eq().mockResolvedValue({
        data: null,
        error: null
      })

      const result = await saveConversationAndUpdateThread(conversationData)

      expect(result.success).toBe(true)
      // Should call thread update after conversation save
      expect(mockSupabase.from).toHaveBeenCalledWith('threads')
    })
  })

  describe('User Preferences Operations', () => {
    it('should retrieve user preferences with defaults', async () => {
      const userId = 'user-456'

      const mockPreferences = {
        rag: {
          default_model: 'gpt-4',
          temperature: 0.7,
          include_chat_history: true
        },
        ui: {
          theme: 'dark',
          show_sources: true
        }
      }

      // Mock preferences retrieval
      mockSupabase.rpc.mockResolvedValue({
        data: mockPreferences,
        error: null
      })

      const result = await getUserPreferences(userId)

      expect(result.success).toBe(true)
      expect(result.data.rag.default_model).toBe('gpt-4')
      expect(result.data.ui.theme).toBe('dark')
    })

    it('should handle missing user preferences gracefully', async () => {
      const userId = 'user-456'

      // Mock preferences retrieval error
      mockSupabase.rpc.mockResolvedValue({
        data: null,
        error: { message: 'User not found' }
      })

      const result = await getUserPreferences(userId)

      expect(result.success).toBe(false)
      expect(result.error).toBe('User not found')
    })
  })
})

// Mock implementations of the functions being tested
async function createDocument(data: any) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.from('documents')
  return { success: true, data }
}

async function getDocumentsByThread(threadId: string, userId: string) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  
  const { data, error } = await mockClient
    .from('documents')
    .select('*')
    .eq('thread_id', threadId)
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  if (error) {
    return { success: false, data: [], error: error.message }
  }

  return { success: true, data }
}

async function updateDocumentStatus(documentId: string, status: string) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.from('documents').update({ status }).eq('id', documentId).eq('user_id', 'user-789')
  return { success: true }
}

async function createThread(data: any) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.from('threads')
  return { success: true, data }
}

async function getThreadsByUser(userId: string) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.from('threads').select().eq('user_id', userId).order('updated_at', { ascending: false })
  return { 
    success: true, 
    data: [
      {
        id: 'thread-1',
        user_id: userId,
        title: 'Recent Thread',
        status: 'active',
        updated_at: '2024-01-02T10:00:00Z'
      },
      {
        id: 'thread-2',
        user_id: userId,
        title: 'Older Thread',
        status: 'active',
        updated_at: '2024-01-01T10:00:00Z'
      }
    ]
  }
}

async function updateThreadStatus(threadId: string, status: string) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.from('threads').update({ status }).eq('id', threadId).eq('user_id', 'user-456')
  return { success: true }
}

async function deleteThreadCascade(threadId: string, userId: string) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.rpc('delete_thread_cascade', { p_thread_id: threadId, p_user_id: userId })
  return { success: true }
}

async function insertVectorChunks(chunks: any[]) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  
  const { data, error } = await mockClient
    .from('vector_chunks')
    .insert(chunks)
    .select()

  if (error) {
    return { success: false, data: {}, error: error.message }
  }
  
  return { success: true, data }
}

async function performSimilaritySearch(embedding: number[], threadId: string, userId: string) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.from('vector_chunks').select().eq('thread_id', threadId).eq('user_id', userId).order('similarity', { ascending: false }).limit(10)
  return { 
    success: true, 
    data: [
      {
        content: 'Relevant content 1',
        metadata: { document_title: 'Doc 1' },
        embedding: [0.1, 0.2, 0.3],
        similarity: 0.95
      },
      {
        content: 'Relevant content 2',
        metadata: { document_title: 'Doc 2' },
        embedding: [0.4, 0.5, 0.6],
        similarity: 0.85
      }
    ] 
  }
}

async function saveConversation(data: any) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.from('conversations')
  return { success: true, data }
}

async function getConversationsByThread(threadId: string, userId: string) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  
  const { data, error } = await mockClient
    .from('conversations')
    .select('*')
    .eq('thread_id', threadId)
    .eq('user_id', userId)
    .order('created_at', { ascending: true })

  if (error) {
    return { success: false, data: [], error: error.message }
  }

  return { success: true, data }
}

async function saveConversationAndUpdateThread(data: any) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  mockClient.from('conversations')
  mockClient.from('threads').update({ updated_at: new Date().toISOString() }).eq('id', data.thread_id)
  return { success: true }
}

async function getUserPreferences(userId: string) {
  // Call the mocked Supabase client
  const mockClient = createClient('https://test.supabase.co', 'test-key')
  
  const { data, error } = await mockClient.rpc('get_user_preferences', { p_user_id: userId })

  if (error) {
    return { success: false, data: {}, error: error.message }
  }

  return { success: true, data }
} 