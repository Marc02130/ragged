import { createClient } from '@supabase/supabase-js'

// Types for Edge Function requests and responses
export interface VectorizationRequest {
  type: 'document' | 'chat_history'
  documentId?: string
  threadId?: string
  userId: string
  content?: string
  metadata?: Record<string, any>
  options?: {
    maxChunks?: number
    batchSize?: number
    chunkSize?: number
    chunkOverlap?: number
  }
}

export interface VectorizationResponse {
  success: boolean
  message: string
  vectorCount?: number
  processedChunks?: number
  totalChunks?: number
  error?: string
}

export interface RAGQueryRequest {
  threadId: string
  userId: string
  query: string
  maxResults?: number
  includeChatHistory?: boolean
  temperature?: number
}

export interface RAGQueryResponse {
  success: boolean
  response?: string
  sources?: Array<{
    content: string
    metadata: Record<string, any>
    similarity: number
  }>
  error?: string
}

export interface DeleteThreadRequest {
  threadId: string
  userId: string
  confirmDeletion: boolean
}

export interface DeleteThreadResponse {
  success: boolean
  message: string
  archivedConversations?: number
  error?: string
}

// Initialize Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL!
const supabase = createClient(supabaseUrl, import.meta.env.VITE_SUPABASE_ANON_KEY!)

/**
 * Get authentication token for Edge Function calls
 */
async function getAuthToken(): Promise<string> {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session?.access_token) {
    throw new Error('No authentication token available')
  }
  return session.access_token
}

/**
 * Make authenticated request to Edge Function
 */
async function callEdgeFunction<T>(
  functionName: string,
  body: any
): Promise<T> {
  const token = await getAuthToken()
  
  const response = await fetch(`${supabaseUrl}/functions/v1/${functionName}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Vectorize a document with optimization options
 */
export async function vectorizeDocument(
  documentId: string, 
  userId: string,
  options?: VectorizationRequest['options']
): Promise<VectorizationResponse> {
  return callEdgeFunction<VectorizationResponse>('vectorize', {
    type: 'document',
    documentId,
    userId,
    options
  })
}

/**
 * Vectorize chat history for a thread with optimization options
 */
export async function vectorizeChatHistory(
  threadId: string, 
  userId: string,
  options?: VectorizationRequest['options']
): Promise<VectorizationResponse> {
  return callEdgeFunction<VectorizationResponse>('vectorize', {
    type: 'chat_history',
    threadId,
    userId,
    options
  })
}

/**
 * Perform RAG query
 */
export async function performRAGQuery(
  threadId: string,
  userId: string,
  query: string,
  options?: {
    maxResults?: number
    includeChatHistory?: boolean
    temperature?: number
  }
): Promise<RAGQueryResponse> {
  return callEdgeFunction<RAGQueryResponse>('rag-query', {
    threadId,
    userId,
    query,
    maxResults: options?.maxResults || 5,
    includeChatHistory: options?.includeChatHistory ?? true,
    temperature: options?.temperature || 0.7
  })
}

/**
 * Delete thread with archival
 */
export async function deleteThread(
  threadId: string,
  userId: string,
  confirmDeletion: boolean = false
): Promise<DeleteThreadResponse> {
  return callEdgeFunction<DeleteThreadResponse>('delete-thread', {
    threadId,
    userId,
    confirmDeletion
  })
}

/**
 * Utility function to check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    await getAuthToken()
    return true
  } catch {
    return false
  }
}

/**
 * Get current user ID
 */
export async function getCurrentUserId(): Promise<string> {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    throw new Error('User not authenticated')
  }
  return user.id
}

/**
 * Error handler for Edge Function calls
 */
export function handleEdgeFunctionError(error: any): string {
  if (error instanceof Error) {
    return error.message
  }
  
  if (typeof error === 'string') {
    return error
  }
  
  if (error?.error) {
    return error.error
  }
  
  return 'An unexpected error occurred'
}

/**
 * Hook for managing Edge Function loading states
 */
export function useEdgeFunctionState() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const executeFunction = async <T>(
    functionCall: () => Promise<T>
  ): Promise<T | null> => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await functionCall()
      return result
    } catch (err) {
      const errorMessage = handleEdgeFunctionError(err)
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    error,
    executeFunction,
    clearError: () => setError(null)
  }
}

// Import React hooks for the custom hook
import { useState } from 'react' 