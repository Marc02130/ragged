import { serve } from "std/http/server"
import { createClient } from '@supabase/supabase-js'
import { OpenAI } from "langchain/llms/openai"
import { OpenAIEmbeddings } from "langchain/embeddings/openai"

// Types for RAG queries
interface RAGQueryRequest {
  threadId: string
  userId: string
  query: string
  maxResults?: number
  includeChatHistory?: boolean
  temperature?: number
}

interface RAGQueryResponse {
  success: boolean
  response?: string
  sources?: Array<{
    content: string
    metadata: Record<string, any>
    similarity: number
  }>
  error?: string
}

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
const supabase = createClient(supabaseUrl, supabaseServiceKey)

// Initialize OpenAI components
const openaiApiKey = Deno.env.get('OPENAI_API_KEY')!
const embeddings = new OpenAIEmbeddings({
  openAIApiKey: openaiApiKey,
  modelName: 'text-embedding-ada-002'
})

const llm = new OpenAI({
  openAIApiKey: openaiApiKey,
  modelName: 'gpt-4',
  temperature: 0.7,
  maxTokens: 1000
})

/**
 * Perform RAG query with similarity search and response generation
 */
async function performRAGQuery(request: RAGQueryRequest): Promise<RAGQueryResponse> {
  try {
    // Generate embedding for the query
    const queryEmbedding = await embeddings.embedQuery(request.query)

    // Build similarity search query
    let similarityQuery = supabase
      .from('vector_chunks')
      .select('content, metadata, embedding')
      .eq('user_id', request.userId)
      .order(`embedding <-> '[${queryEmbedding.join(',')}]'::vector`, { ascending: true })
      .limit(request.maxResults || 5)

    // Filter by thread if specified
    if (request.threadId) {
      similarityQuery = similarityQuery.eq('metadata->thread_id', request.threadId)
    }

    // Optionally include chat history
    if (!request.includeChatHistory) {
      similarityQuery = similarityQuery.neq('metadata->is_chat_history', true)
    }

    // Execute similarity search
    const { data: similarChunks, error: searchError } = await similarityQuery

    if (searchError) {
      return {
        success: false,
        error: `Similarity search failed: ${searchError.message}`
      }
    }

    if (!similarChunks || similarChunks.length === 0) {
      return {
        success: false,
        error: 'No relevant content found for your query'
      }
    }

    // Prepare context from similar chunks
    const context = similarChunks
      .map(chunk => chunk.content)
      .join('\n\n---\n\n')

    // Create prompt for RAG response
    const prompt = createRAGPrompt(request.query, context, similarChunks)

    // Generate response using OpenAI
    const response = await llm.call(prompt)

    // Calculate similarity scores for sources
    const sources = similarChunks.map(chunk => ({
      content: chunk.content.substring(0, 200) + (chunk.content.length > 200 ? '...' : ''),
      metadata: chunk.metadata,
      similarity: calculateCosineSimilarity(queryEmbedding, chunk.embedding)
    }))

    return {
      success: true,
      response: response.trim(),
      sources
    }

  } catch (error) {
    console.error('RAG query error:', error)
    return {
      success: false,
      error: `RAG query failed: ${error.message}`
    }
  }
}

/**
 * Create a comprehensive prompt for RAG response generation
 */
function createRAGPrompt(query: string, context: string, sources: any[]): string {
  const sourceInfo = sources.map((source, index) => {
    const metadata = source.metadata
    let sourceType = 'Document'
    let sourceName = metadata.document_title || metadata.file_name || 'Unknown'
    
    if (metadata.is_chat_history) {
      sourceType = 'Chat History'
      sourceName = `Conversation from ${new Date(metadata.date_range?.start).toLocaleDateString()}`
    } else if (metadata.is_thread_archive) {
      sourceType = 'Thread Archive'
      sourceName = metadata.thread_title || 'Unknown Thread'
    }

    return `Source ${index + 1} (${sourceType} - ${sourceName}):\n${source.content}`
  }).join('\n\n')

  return `You are a helpful AI assistant that answers questions based on the provided context. Use only the information from the sources below to answer the user's question. If the sources don't contain enough information to answer the question, say so.

Context Sources:
${sourceInfo}

User Question: ${query}

Instructions:
1. Answer the question based only on the provided context
2. Be concise but comprehensive
3. If you reference specific information, mention which source it came from
4. If the context doesn't contain enough information, acknowledge this limitation
5. Use a helpful and professional tone

Answer:`
}

/**
 * Calculate cosine similarity between two vectors
 */
function calculateCosineSimilarity(vec1: number[], vec2: number[]): number {
  if (vec1.length !== vec2.length) {
    return 0
  }

  let dotProduct = 0
  let norm1 = 0
  let norm2 = 0

  for (let i = 0; i < vec1.length; i++) {
    dotProduct += vec1[i] * vec2[i]
    norm1 += vec1[i] * vec1[i]
    norm2 += vec2[i] * vec2[i]
  }

  norm1 = Math.sqrt(norm1)
  norm2 = Math.sqrt(norm2)

  if (norm1 === 0 || norm2 === 0) {
    return 0
  }

  return dotProduct / (norm1 * norm2)
}

/**
 * Save conversation to database
 */
async function saveConversation(threadId: string, userId: string, role: string, content: string): Promise<void> {
  try {
    await supabase
      .from('conversations')
      .insert({
        thread_id: threadId,
        user_id: userId,
        role,
        content,
        metadata: {
          timestamp: new Date().toISOString()
        }
      })

    // Update thread's last activity
    await supabase
      .from('threads')
      .update({ 
        last_activity_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', threadId)

  } catch (error) {
    console.error('Failed to save conversation:', error)
    // Don't fail the entire request if saving fails
  }
}

/**
 * Main Edge Function handler
 */
serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      }
    })
  }

  try {
    // Verify authentication
    const authHeader = req.headers.get('authorization')
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: 'Authorization header required' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Get user from JWT token
    const { data: { user }, error: authError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''))
    
    if (authError || !user) {
      return new Response(
        JSON.stringify({ error: 'Invalid authentication token' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Parse request body
    const requestData: RAGQueryRequest = await req.json()
    
    if (!requestData.threadId || !requestData.userId || !requestData.query) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: threadId, userId, and query' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Verify user owns the thread
    if (requestData.userId !== user.id) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized access to thread' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Verify thread exists and belongs to user
    const { data: thread, error: threadError } = await supabase
      .from('threads')
      .select('id')
      .eq('id', requestData.threadId)
      .eq('user_id', requestData.userId)
      .single()

    if (threadError || !thread) {
      return new Response(
        JSON.stringify({ error: 'Thread not found or access denied' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Save user query to conversation history
    await saveConversation(requestData.threadId, requestData.userId, 'user', requestData.query)

    // Perform RAG query
    const result = await performRAGQuery(requestData)

    if (result.success && result.response) {
      // Save AI response to conversation history
      await saveConversation(requestData.threadId, requestData.userId, 'assistant', result.response)
    }

    return new Response(
      JSON.stringify(result),
      { 
        status: result.success ? 200 : 500,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )

  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(
      JSON.stringify({ 
        success: false,
        error: 'Internal server error'
      }),
      { 
        status: 500,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )
  }
}) 