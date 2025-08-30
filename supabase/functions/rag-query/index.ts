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
  model?: string
  includeThreadContext?: boolean
  searchStrategy?: 'hybrid' | 'semantic' | 'keyword'
  responseFormat?: 'text' | 'structured'
  // Retrieval filtering options
  topKPerThread?: number
  maxThreadsSearch?: number
  crossThreadSearch?: boolean
  currentThreadPriority?: boolean
}

// User preferences interface
interface UserPreferences {
  rag?: {
    default_model?: string
    temperature?: number
    max_tokens?: number
    include_chat_history?: boolean
    cross_thread_search?: boolean
    similarity_threshold?: number
  }
  ui?: {
    theme?: string
    compact_mode?: boolean
    show_sources?: boolean
    auto_scroll?: boolean
  }
  notifications?: {
    email_notifications?: boolean
    processing_complete?: boolean
    error_alerts?: boolean
  }
}

interface RAGQueryResponse {
  success: boolean
  response?: string
  sources?: Array<{
    content: string
    metadata: Record<string, any>
    similarity: number
    sourceType: 'document' | 'chat_history' | 'thread_archive'
  }>
  conversationId?: string
  threadContext?: {
    threadId: string
    threadTitle: string
    conversationCount: number
    lastActivity: string
  }
  performance?: {
    searchTime: number
    generationTime: number
    totalTime: number
    tokensUsed: number
  }
  fallbackGenerated?: boolean
  error?: string
}

// Configuration constants for RAG queries
const RAG_CONFIG = {
  DEFAULT_MAX_RESULTS: 8,
  DEFAULT_TEMPERATURE: 0.7,
  DEFAULT_MODEL: 'gpt-4',
  MAX_TOKENS: 2000,
  SIMILARITY_THRESHOLD: 0.7,
  CONTEXT_WINDOW_SIZE: 4000,
  CHAT_HISTORY_WEIGHT: 0.8,
  DOCUMENT_WEIGHT: 1.0,
  THREAD_ARCHIVE_WEIGHT: 0.9,
  // Retrieval filtering configuration
  TOP_K_PER_THREAD: 3, // Number of top chunks per thread
  MAX_THREADS_SEARCH: 5, // Maximum number of threads to search
  CROSS_THREAD_WEIGHT: 0.9, // Weight for cross-thread results
  CURRENT_THREAD_WEIGHT: 1.0, // Weight for current thread results
  MIN_SIMILARITY_CROSS_THREAD: 0.8, // Higher threshold for cross-thread results
  // Fallback configuration
  AUTO_VECTORIZE_FALLBACK: true, // Auto-vectorize fallback conversations
  FALLBACK_TEMPERATURE: 0.8, // Higher temperature for fallback responses
  FALLBACK_MAX_TOKENS: 1500, // Shorter responses for fallbacks
} as const

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
 * Enhanced authentication and user preferences validation
 */
async function validateAuthAndGetPreferences(authHeader: string): Promise<{ user: any; preferences: UserPreferences; error?: string }> {
  try {
    console.log(`[AUTH] Validating authentication...`)
    
    if (!authHeader) {
      return { user: null, preferences: {}, error: 'Authorization header required' }
    }

    // Get user from JWT token
    const { data: { user }, error: authError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''))
    
    if (authError || !user) {
      console.error(`[AUTH] ❌ Authentication failed:`, authError?.message)
      return { user: null, preferences: {}, error: 'Invalid authentication token' }
    }

    console.log(`[AUTH] ✅ Authentication successful for user: ${user.id}`)

    // Get user preferences from database
    console.log(`[AUTH] Fetching user preferences...`)
    const { data: preferences, error: prefsError } = await supabase
      .rpc('get_user_preferences', { p_user_id: user.id })

    if (prefsError) {
      console.warn(`[AUTH] ⚠️ Failed to fetch user preferences:`, prefsError.message)
      // Continue with default preferences
      return { 
        user, 
        preferences: {
          rag: {
            default_model: 'gpt-4',
            temperature: 0.7,
            max_tokens: 1000,
            include_chat_history: true,
            cross_thread_search: true,
            similarity_threshold: 0.7
          }
        }
      }
    }

    console.log(`[AUTH] ✅ User preferences loaded successfully`)
    return { user, preferences: preferences || {} }

  } catch (error) {
    console.error(`[AUTH] ❌ Authentication validation error:`, error)
    return { user: null, preferences: {}, error: 'Authentication validation failed' }
  }
}

/**
 * Perform RAG query with enhanced similarity search and response generation
 */
async function performRAGQuery(request: RAGQueryRequest): Promise<RAGQueryResponse> {
  const startTime = Date.now()
  console.log(`[RAG QUERY] 🚀 Starting RAG query for thread ${request.threadId}, user ${request.userId}`)
  console.log(`[RAG QUERY] Query: "${request.query}"`)
  
  try {
    // Get thread context if requested
    let threadContext = null
    if (request.includeThreadContext) {
      console.log(`[RAG QUERY] Fetching thread context...`)
      threadContext = await getThreadContext(request.threadId, request.userId)
    }

    // Generate embedding for the query
    console.log(`[RAG QUERY] Generating query embedding...`)
    const queryStartTime = Date.now()
    const queryEmbedding = await embeddings.embedQuery(request.query)
    const queryEndTime = Date.now()
    console.log(`[RAG QUERY] Query embedding generated in ${queryEndTime - queryStartTime}ms`)

    // Perform similarity search with enhanced filtering
    console.log(`[RAG QUERY] Performing similarity search...`)
    const searchStartTime = Date.now()
    const similarChunks = await performSimilaritySearch(request, queryEmbedding)
    const searchEndTime = Date.now()
    const searchTime = searchEndTime - searchStartTime
    
    console.log(`[RAG QUERY] Similarity search completed in ${searchTime}ms, found ${similarChunks.length} chunks`)

    if (similarChunks.length === 0) {
      console.log(`[RAG QUERY] No relevant chunks found, generating fallback response...`)
      
      // Generate fallback response
      const fallbackResponse = await generateFallbackResponse(request.query, threadContext)
      
      // Save conversation to database
      console.log(`[RAG QUERY] Saving fallback conversation to database...`)
      const conversationId = await saveConversation(request.threadId, request.userId, 'user', request.query)
      await saveConversation(request.threadId, request.userId, 'assistant', fallbackResponse.response)
      
      // Optionally vectorize the new conversation for future reference
      if (RAG_CONFIG.AUTO_VECTORIZE_FALLBACK) {
        console.log(`[RAG QUERY] Auto-vectorizing fallback conversation...`)
        try {
          await vectorizeFallbackConversation(request.threadId, request.userId, request.query, fallbackResponse.response)
        } catch (vectorizeError) {
          console.warn(`[RAG QUERY] Failed to vectorize fallback conversation:`, vectorizeError)
        }
      }
      
      const totalTime = Date.now() - startTime
      
      console.log(`[RAG QUERY] ✅ Fallback response generated successfully!`)
      console.log(`[RAG QUERY] 📊 Performance:`, {
        searchTime,
        generationTime: fallbackResponse.generationTime,
        totalTime,
        tokensUsed: fallbackResponse.tokensUsed,
        chunksFound: 0,
        sourcesReturned: 0,
        fallbackGenerated: true
      })
      
      return {
        success: true,
        response: fallbackResponse.response,
        sources: [],
        conversationId,
        threadContext,
        performance: {
          searchTime,
          generationTime: fallbackResponse.generationTime,
          totalTime,
          tokensUsed: fallbackResponse.tokensUsed
        },
        fallbackGenerated: true
      }
    }

    // Prepare weighted context from similar chunks
    console.log(`[RAG QUERY] Preparing context from ${similarChunks.length} chunks...`)
    const context = prepareWeightedContext(similarChunks, request.query)

    // Create enhanced prompt for RAG response
    console.log(`[RAG QUERY] Creating RAG prompt...`)
    const prompt = createEnhancedRAGPrompt(request.query, context, similarChunks, threadContext)

    // Generate response using OpenAI with performance tracking
    console.log(`[RAG QUERY] Generating response with ${request.model || RAG_CONFIG.DEFAULT_MODEL}...`)
    const generationStartTime = Date.now()
    const response = await generateResponse(prompt, request)
    const generationEndTime = Date.now()
    const generationTime = generationEndTime - generationStartTime
    
    console.log(`[RAG QUERY] Response generated in ${generationTime}ms`)

    // Save conversation to database
    console.log(`[RAG QUERY] Saving conversation to database...`)
    const conversationId = await saveConversation(request.threadId, request.userId, 'user', request.query)
    await saveConversation(request.threadId, request.userId, 'assistant', response.response)

    // Prepare sources with enhanced metadata
    const sources = similarChunks.map(chunk => ({
      content: chunk.content.substring(0, 200) + (chunk.content.length > 200 ? '...' : ''),
      metadata: chunk.metadata,
      similarity: calculateCosineSimilarity(queryEmbedding, chunk.embedding),
      sourceType: determineSourceType(chunk.metadata)
    }))

    const totalTime = Date.now() - startTime
    
    console.log(`[RAG QUERY] ✅ RAG query completed successfully!`)
    console.log(`[RAG QUERY] 📊 Performance:`, {
      searchTime,
      generationTime,
      totalTime,
      tokensUsed: response.tokensUsed,
      chunksFound: similarChunks.length,
      sourcesReturned: sources.length
    })

    return {
      success: true,
      response: response.response,
      sources,
      conversationId,
      threadContext,
      performance: {
        searchTime,
        generationTime,
        totalTime,
        tokensUsed: response.tokensUsed
      }
    }

  } catch (error) {
    const totalTime = Date.now() - startTime
    console.error(`[RAG QUERY] ❌ RAG query failed after ${totalTime}ms:`, error)
    return {
      success: false,
      error: `RAG query failed: ${error.message}`,
      performance: {
        searchTime: 0,
        generationTime: 0,
        totalTime,
        tokensUsed: 0
      }
    }
  }
}

/**
 * Get thread context information
 */
async function getThreadContext(threadId: string, userId: string) {
  try {
    const { data: thread, error } = await supabase
      .from('threads')
      .select('id, title, created_at, updated_at')
      .eq('id', threadId)
      .eq('user_id', userId)
      .single()

    if (error || !thread) {
      console.warn(`[RAG QUERY] Thread context not found: ${error?.message}`)
      return null
    }

    // Get conversation count
    const { count: conversationCount } = await supabase
      .from('conversations')
      .select('*', { count: 'exact', head: true })
      .eq('thread_id', threadId)
      .eq('user_id', userId)

    return {
      threadId: thread.id,
      threadTitle: thread.title,
      conversationCount: conversationCount || 0,
      lastActivity: thread.updated_at
    }
  } catch (error) {
    console.error(`[RAG QUERY] Error fetching thread context:`, error)
    return null
  }
}

/**
 * Perform enhanced similarity search with top-k retrieval filtering across threads
 */
async function performSimilaritySearch(request: RAGQueryRequest, queryEmbedding: number[]) {
  const maxResults = request.maxResults || RAG_CONFIG.DEFAULT_MAX_RESULTS
  
  // Use request options or defaults
  const topKPerThread = request.topKPerThread || RAG_CONFIG.TOP_K_PER_THREAD
  const maxThreadsSearch = request.maxThreadsSearch || RAG_CONFIG.MAX_THREADS_SEARCH
  const crossThreadSearch = request.crossThreadSearch !== false // Default to true
  const currentThreadPriority = request.currentThreadPriority !== false // Default to true

  console.log(`[RAG QUERY] Starting enhanced similarity search with top-k filtering`)
  console.log(`[RAG QUERY] Configuration:`, {
    maxResults,
    topKPerThread,
    maxThreadsSearch,
    crossThreadSearch,
    currentThreadPriority,
    currentThreadId: request.threadId
  })

  try {
    // Determine which threads to search
    let threadsToSearch: any[] = []

    if (crossThreadSearch) {
      // Get user's threads for cross-thread search
      const { data: userThreads, error: threadsError } = await supabase
        .from('threads')
        .select('id, title, created_at')
        .eq('user_id', request.userId)
        .order('updated_at', { ascending: false })
        .limit(maxThreadsSearch)

      if (threadsError) {
        throw new Error(`Failed to fetch user threads: ${threadsError.message}`)
      }

      if (!userThreads || userThreads.length === 0) {
        console.warn(`[RAG QUERY] No threads found for user ${request.userId}`)
        return []
      }

      threadsToSearch = userThreads
      console.log(`[RAG QUERY] Found ${userThreads.length} threads for cross-thread search`)
    } else {
      // Search only current thread
      const { data: currentThread, error: threadError } = await supabase
        .from('threads')
        .select('id, title, created_at')
        .eq('id', request.threadId)
        .eq('user_id', request.userId)
        .single()

      if (threadError || !currentThread) {
        throw new Error(`Failed to fetch current thread: ${threadError?.message}`)
      }

      threadsToSearch = [currentThread]
      console.log(`[RAG QUERY] Searching only current thread: ${currentThread.title}`)
    }

    console.log(`[RAG QUERY] Found ${threadsToSearch.length} threads for search`)

    // Perform similarity search for each thread
    const threadResults: Array<{
      threadId: string
      threadTitle: string
      chunks: any[]
      totalChunks: number
    }> = []

    for (const thread of threadsToSearch) {
      console.log(`[RAG QUERY] Searching thread: ${thread.title} (${thread.id})`)
      
      // Build similarity search query for this thread
      let threadQuery = supabase
        .from('vector_chunks')
        .select('content, metadata, embedding, thread_id')
        .eq('user_id', request.userId)
        .eq('thread_id', thread.id)
        .order(`embedding <-> '[${queryEmbedding.join(',')}]'::vector`, { ascending: true })
        .limit(RAG_CONFIG.TOP_K_PER_THREAD * 2) // Get more for filtering

      // Apply chat history filtering if requested
      if (!request.includeChatHistory) {
        threadQuery = threadQuery.neq('metadata->is_chat_history', true)
      }

      // Execute search for this thread
      const { data: threadChunks, error: threadSearchError } = await threadQuery

      if (threadSearchError) {
        console.error(`[RAG QUERY] Error searching thread ${thread.id}:`, threadSearchError)
        continue
      }

      if (!threadChunks || threadChunks.length === 0) {
        console.log(`[RAG QUERY] No chunks found in thread ${thread.title}`)
        continue
      }

      // Calculate similarity scores for this thread's chunks
      const scoredChunks = threadChunks.map(chunk => ({
        ...chunk,
        similarity: calculateCosineSimilarity(queryEmbedding, chunk.embedding),
        threadId: thread.id,
        threadTitle: thread.title
      }))

      // Apply similarity threshold (higher for cross-thread results)
      const threshold = thread.id === request.threadId 
        ? RAG_CONFIG.SIMILARITY_THRESHOLD 
        : RAG_CONFIG.MIN_SIMILARITY_CROSS_THREAD

      const filteredChunks = scoredChunks.filter(chunk => chunk.similarity >= threshold)

      // Apply source type weighting
      const weightedChunks = filteredChunks.map(chunk => ({
        ...chunk,
        weight: calculateSourceWeight(chunk.metadata)
      }))

      // Sort by weighted score and take top-k
      const topKChunks = weightedChunks
        .sort((a, b) => (b.similarity * b.weight) - (a.similarity * a.weight))
        .slice(0, RAG_CONFIG.TOP_K_PER_THREAD)

      threadResults.push({
        threadId: thread.id,
        threadTitle: thread.title,
        chunks: topKChunks,
        totalChunks: threadChunks.length
      })

      console.log(`[RAG QUERY] Thread ${thread.title}: ${topKChunks.length}/${threadChunks.length} chunks selected`)
    }

    // Combine and rank all thread results
    const allChunks = threadResults.flatMap(result => result.chunks)

    if (allChunks.length === 0) {
      console.warn(`[RAG QUERY] No relevant chunks found across all threads`)
      return []
    }

    // Apply cross-thread weighting based on priority settings
    const crossThreadWeightedChunks = allChunks.map(chunk => {
      const isCurrentThread = chunk.threadId === request.threadId
      
      let threadWeight = RAG_CONFIG.CROSS_THREAD_WEIGHT
      if (isCurrentThread && currentThreadPriority) {
        threadWeight = RAG_CONFIG.CURRENT_THREAD_WEIGHT
      } else if (isCurrentThread && !currentThreadPriority) {
        threadWeight = RAG_CONFIG.CROSS_THREAD_WEIGHT
      }

      return {
        ...chunk,
        finalWeight: chunk.weight * threadWeight,
        isCurrentThread
      }
    })

    // Sort by final weighted score and limit to max results
    const finalResults = crossThreadWeightedChunks
      .sort((a, b) => (b.similarity * b.finalWeight) - (a.similarity * a.finalWeight))
      .slice(0, maxResults)

    // Log detailed results
    const currentThreadResults = finalResults.filter(chunk => chunk.isCurrentThread)
    const crossThreadResults = finalResults.filter(chunk => !chunk.isCurrentThread)

    console.log(`[RAG QUERY] Enhanced similarity search completed:`, {
      threadsSearched: threadResults.length,
      totalChunksFound: allChunks.length,
      finalResults: finalResults.length,
      currentThreadResults: currentThreadResults.length,
      crossThreadResults: crossThreadResults.length,
      averageSimilarity: finalResults.reduce((sum, chunk) => sum + chunk.similarity, 0) / finalResults.length,
      threadBreakdown: threadResults.map(r => ({
        thread: r.threadTitle,
        selected: r.chunks.length,
        total: r.totalChunks
      }))
    })

    return finalResults

  } catch (error) {
    console.error(`[RAG QUERY] Enhanced similarity search failed:`, error)
    throw new Error(`Enhanced similarity search failed: ${error.message}`)
  }
}

/**
 * Calculate source weight based on metadata
 */
function calculateSourceWeight(metadata: any): number {
  if (metadata.is_chat_history) {
    return RAG_CONFIG.CHAT_HISTORY_WEIGHT
  } else if (metadata.is_thread_archive) {
    return RAG_CONFIG.THREAD_ARCHIVE_WEIGHT
  } else {
    return RAG_CONFIG.DOCUMENT_WEIGHT
  }
}

/**
 * Prepare weighted context from similar chunks
 */
function prepareWeightedContext(chunks: any[], query: string): string {
  // Sort chunks by relevance and weight
  const sortedChunks = chunks.sort((a, b) => 
    (b.similarity * b.weight) - (a.similarity * a.weight)
  )

  // Build context with source information
  const contextParts = sortedChunks.map((chunk, index) => {
    const sourceType = determineSourceType(chunk.metadata)
    const sourceInfo = getSourceInfo(chunk.metadata, sourceType)
    
    return `[Source ${index + 1} - ${sourceInfo}]\n${chunk.content}`
  })

  // Join with separators and limit context size
  let context = contextParts.join('\n\n---\n\n')
  
  // Truncate if context is too large
  if (context.length > RAG_CONFIG.CONTEXT_WINDOW_SIZE) {
    context = context.substring(0, RAG_CONFIG.CONTEXT_WINDOW_SIZE) + '...'
    console.log(`[RAG QUERY] Context truncated to ${RAG_CONFIG.CONTEXT_WINDOW_SIZE} characters`)
  }

  return context
}

/**
 * Determine source type from metadata
 */
function determineSourceType(metadata: any): 'document' | 'chat_history' | 'thread_archive' {
  if (metadata.is_chat_history) {
    return 'chat_history'
  } else if (metadata.is_thread_archive) {
    return 'thread_archive'
  } else {
    return 'document'
  }
}

/**
 * Get source information for display
 */
function getSourceInfo(metadata: any, sourceType: string): string {
  switch (sourceType) {
    case 'document':
      return `Document: ${metadata.document_title || metadata.file_name || 'Unknown'}`
    case 'chat_history':
      const date = metadata.date_range?.start ? new Date(metadata.date_range.start).toLocaleDateString() : 'Unknown'
      return `Chat History: ${date} (${metadata.conversation_count || 0} messages)`
    case 'thread_archive':
      return `Thread Archive: ${metadata.thread_title || 'Unknown Thread'}`
    default:
      return 'Unknown Source'
  }
}

/**
 * Create enhanced RAG prompt with thread context
 */
function createEnhancedRAGPrompt(
  query: string, 
  context: string, 
  sources: any[], 
  threadContext: any
): string {
  let prompt = `You are a helpful AI assistant that answers questions based on the provided context. Use only the information from the sources below to answer the user's question. If the sources don't contain enough information to answer the question, say so.

`

  // Add thread context if available
  if (threadContext) {
    prompt += `Thread Context:
- Thread: ${threadContext.threadTitle}
- Total Conversations: ${threadContext.conversationCount}
- Last Activity: ${new Date(threadContext.lastActivity).toLocaleString()}

`
  }

  prompt += `Context Sources:
${context}

User Question: ${query}

Instructions:
1. Answer the question based only on the provided context
2. Be concise but comprehensive
3. If you reference specific information, mention which source it came from
4. If the context doesn't contain enough information, acknowledge this limitation
5. Use a helpful and professional tone
6. Consider the thread context when providing relevant responses

Answer:`

  return prompt
}

/**
 * Generate fallback response when no relevant content is found
 */
async function generateFallbackResponse(query: string, threadContext: any) {
  const fallbackPrompt = createFallbackPrompt(query, threadContext)
  
  // Create LLM instance with fallback settings
  const llm = new OpenAI({
    openAIApiKey: openaiApiKey,
    modelName: RAG_CONFIG.DEFAULT_MODEL,
    temperature: RAG_CONFIG.FALLBACK_TEMPERATURE,
    maxTokens: RAG_CONFIG.FALLBACK_MAX_TOKENS
  })

  try {
    const startTime = Date.now()
    const response = await llm.call(fallbackPrompt)
    const endTime = Date.now()
    
    // Estimate token usage
    const tokensUsed = Math.ceil((fallbackPrompt.length + response.length) / 4)
    
    return {
      response: response.trim(),
      tokensUsed,
      generationTime: endTime - startTime
    }
  } catch (error) {
    console.error(`[RAG QUERY] Fallback response generation error:`, error)
    throw new Error(`Failed to generate fallback response: ${error.message}`)
  }
}

/**
 * Create fallback prompt for when no relevant content is found
 */
function createFallbackPrompt(query: string, threadContext: any): string {
  let prompt = `You are a helpful AI assistant. The user has asked a question, but I don't have any relevant documents or previous conversations to reference for this specific query.

User Question: ${query}

`

  if (threadContext) {
    prompt += `Thread Context:
- Thread: ${threadContext.threadTitle}
- Total Conversations: ${threadContext.conversationCount}
- Last Activity: ${new Date(threadContext.lastActivity).toLocaleString()}

`
  }

  prompt += `Instructions:
1. Provide a helpful and informative response based on your general knowledge
2. Be honest about not having specific context from their documents or previous conversations
3. Offer to help them with related topics or suggest how they might find the information
4. Keep the response concise but helpful
5. Use a friendly and professional tone

Response:`

  return prompt
}

/**
 * Vectorize fallback conversation for future reference
 */
async function vectorizeFallbackConversation(
  threadId: string, 
  userId: string, 
  userQuery: string, 
  assistantResponse: string
) {
  try {
    console.log(`[RAG QUERY] Vectorizing fallback conversation for thread ${threadId}`)
    
    // Create conversation text for vectorization
    const conversationText = `User: ${userQuery}\n\nAssistant: ${assistantResponse}`
    
    // Generate embedding for the conversation
    const embedding = await embeddings.embedQuery(conversationText)
    
    // Prepare vector chunk for insertion
    const vectorChunk = {
      document_id: null, // No specific document
      user_id: userId,
      thread_id: threadId,
      content: conversationText,
      embedding: embedding,
      metadata: {
        is_chat_history: true,
        is_fallback_conversation: true,
        user_query: userQuery,
        assistant_response: assistantResponse,
        conversation_type: 'fallback',
        processing_timestamp: new Date().toISOString(),
        chunk_index: 0,
        chunk_size: conversationText.length
      },
      chunk_index: 0
    }
    
    // Insert the vector chunk
    const { error: insertError } = await supabase
      .from('vector_chunks')
      .insert(vectorChunk)
    
    if (insertError) {
      throw new Error(`Failed to insert fallback vector chunk: ${insertError.message}`)
    }
    
    console.log(`[RAG QUERY] ✅ Fallback conversation vectorized successfully`)
    
  } catch (error) {
    console.error(`[RAG QUERY] Error vectorizing fallback conversation:`, error)
    throw error
  }
}

/**
 * Generate response with OpenAI and track token usage
 */
async function generateResponse(prompt: string, request: RAGQueryRequest) {
  const model = request.model || RAG_CONFIG.DEFAULT_MODEL
  const temperature = request.temperature || RAG_CONFIG.DEFAULT_TEMPERATURE

  // Create LLM instance with specific model
  const llm = new OpenAI({
    openAIApiKey: openaiApiKey,
    modelName: model,
    temperature,
    maxTokens: RAG_CONFIG.MAX_TOKENS
  })

  try {
    const response = await llm.call(prompt)
    
    // Estimate token usage (rough approximation)
    const tokensUsed = Math.ceil((prompt.length + response.length) / 4)
    
    return {
      response: response.trim(),
      tokensUsed
    }
  } catch (error) {
    console.error(`[RAG QUERY] Response generation error:`, error)
    throw new Error(`Failed to generate response: ${error.message}`)
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
 * Save conversation to database and return conversation ID
 */
async function saveConversation(threadId: string, userId: string, role: string, content: string): Promise<string> {
  try {
    const { data: conversation, error } = await supabase
      .from('conversations')
      .insert({
        thread_id: threadId,
        user_id: userId,
        role,
        content,
        metadata: {
          timestamp: new Date().toISOString(),
          query_type: 'rag'
        }
      })
      .select('id')
      .single()

    if (error) {
      throw error
    }

    // Update thread's last activity
    await supabase
      .from('threads')
      .update({ 
        last_activity_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .eq('id', threadId)

    console.log(`[RAG QUERY] Saved ${role} conversation: ${conversation.id}`)
    return conversation.id

  } catch (error) {
    console.error(`[RAG QUERY] Failed to save conversation:`, error)
    // Don't fail the entire request if saving fails
    return ''
  }
}

/**
 * Main Edge Function handler
 */
serve(async (req) => {
  const requestStartTime = Date.now()
  console.log(`[RAG EDGE FUNCTION] 🚀 RAG query request received: ${req.method} ${req.url}`)
  
  // Handle CORS
  if (req.method === 'OPTIONS') {
    console.log(`[RAG EDGE FUNCTION] Handling CORS preflight request`)
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      }
    })
  }

  try {
    console.log(`[RAG EDGE FUNCTION] Verifying authentication and loading user preferences...`)
    
    // Enhanced authentication with user preferences
    const authHeader = req.headers.get('authorization')
    const { user, preferences, error: authError } = await validateAuthAndGetPreferences(authHeader || '')
    
    if (authError || !user) {
      console.error(`[RAG EDGE FUNCTION] ❌ Authentication failed:`, authError)
      return new Response(
        JSON.stringify({ error: authError || 'Authentication failed' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log(`[RAG EDGE FUNCTION] ✅ Authentication and preferences loaded for user: ${user.id}`)

    // Parse request body
    console.log(`[RAG EDGE FUNCTION] Parsing request body...`)
    const requestData: RAGQueryRequest = await req.json()
    
    if (!requestData.threadId || !requestData.userId || !requestData.query) {
      console.error(`[RAG EDGE FUNCTION] ❌ Missing required fields:`, { 
        threadId: requestData.threadId, 
        userId: requestData.userId, 
        query: requestData.query ? 'provided' : 'missing' 
      })
      return new Response(
        JSON.stringify({ error: 'Missing required fields: threadId, userId, and query' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Verify user owns the thread
    if (requestData.userId !== user.id) {
      console.error(`[RAG EDGE FUNCTION] ❌ Unauthorized access: requested user ${requestData.userId} != authenticated user ${user.id}`)
      return new Response(
        JSON.stringify({ error: 'Unauthorized access to thread' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log(`[RAG EDGE FUNCTION] Processing RAG query for thread ${requestData.threadId}`)
    if (requestData.model || requestData.temperature !== undefined || requestData.includeChatHistory !== undefined) {
      console.log(`[RAG EDGE FUNCTION] Custom options:`, {
        model: requestData.model,
        temperature: requestData.temperature,
        includeChatHistory: requestData.includeChatHistory,
        includeThreadContext: requestData.includeThreadContext
      })
    }

    // Verify thread exists and belongs to user
    const { data: thread, error: threadError } = await supabase
      .from('threads')
      .select('id')
      .eq('id', requestData.threadId)
      .eq('user_id', requestData.userId)
      .single()

    if (threadError || !thread) {
      console.error(`[RAG EDGE FUNCTION] ❌ Thread not found or access denied:`, threadError?.message)
      return new Response(
        JSON.stringify({ error: 'Thread not found or access denied' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log(`[RAG EDGE FUNCTION] ✅ Thread access verified`)

    // Perform RAG query with enhanced functionality
    const result = await performRAGQuery(requestData)

    const requestEndTime = Date.now()
    const totalRequestTime = requestEndTime - requestStartTime
    
    console.log(`[RAG EDGE FUNCTION] 📊 Request completed in ${totalRequestTime}ms:`, {
      threadId: requestData.threadId,
      userId: requestData.userId,
      success: result.success,
      responseLength: result.response?.length || 0,
      sourcesCount: result.sources?.length || 0,
      performance: result.performance
    })

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
    const requestEndTime = Date.now()
    const totalRequestTime = requestEndTime - requestStartTime
    
    console.error(`[RAG EDGE FUNCTION] ❌ Request failed after ${totalRequestTime}ms:`, error)
    return new Response(
      JSON.stringify({ 
        success: false,
        error: 'Internal server error',
        details: error.message
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