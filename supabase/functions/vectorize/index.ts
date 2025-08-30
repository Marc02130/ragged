import { serve } from "std/http/server"
import { createClient } from '@supabase/supabase-js'
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter"
import { OpenAIEmbeddings } from "langchain/embeddings/openai"
import { Document } from "langchain/document"

// Types for the vectorization process
interface VectorizationRequest {
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

interface VectorizationResponse {
  success: boolean
  message: string
  vectorCount?: number
  processedChunks?: number
  totalChunks?: number
  error?: string
}

// Configuration constants for large document optimization
const VECTORIZATION_CONFIG = {
  MAX_CHUNKS_PER_DOCUMENT: 1000, // Limit chunks per document
  BATCH_SIZE: 100, // Insert chunks in batches of 100
  DEFAULT_CHUNK_SIZE: 1000,
  DEFAULT_CHUNK_OVERLAP: 200,
  MAX_EMBEDDING_BATCH_SIZE: 50, // OpenAI API limit for embeddings
  MAX_CONTENT_LENGTH: 1000000, // 1MB content limit
  RATE_LIMIT_DELAY: 1000, // 1 second delay between batches
} as const

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
const supabase = createClient(supabaseUrl, supabaseServiceKey)

// Initialize OpenAI embeddings
const openaiApiKey = Deno.env.get('OPENAI_API_KEY')!
const embeddings = new OpenAIEmbeddings({
  openAIApiKey: openaiApiKey,
  modelName: 'text-embedding-ada-002'
})

/**
 * Process and vectorize uploaded documents with optimization for large documents
 */
async function vectorizeDocument(
  documentId: string, 
  userId: string, 
  options?: VectorizationRequest['options']
): Promise<VectorizationResponse> {
  const startTime = Date.now()
  console.log(`[DOCUMENT VECTORIZATION] Starting vectorization for document ${documentId}, user ${userId}`)
  
  try {
    console.log(`[DOCUMENT VECTORIZATION] Fetching document content from database...`)
    
    // Fetch document content from Supabase with RLS enforcement
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .eq('user_id', userId)
      .single()

    if (docError || !document) {
      console.error(`[DOCUMENT VECTORIZATION] Document fetch failed:`, docError?.message)
      return {
        success: false,
        message: 'Document not found or access denied',
        error: docError?.message
      }
    }

    console.log(`[DOCUMENT VECTORIZATION] Document found: "${document.title}" (${document.content?.length || 0} characters)`)

    if (!document.content) {
      console.warn(`[DOCUMENT VECTORIZATION] Document has no content to vectorize`)
      return {
        success: false,
        message: 'Document has no content to vectorize',
        error: 'No content available'
      }
    }

    // Check content length limit
    if (document.content.length > VECTORIZATION_CONFIG.MAX_CONTENT_LENGTH) {
      console.error(`[DOCUMENT VECTORIZATION] Content length ${document.content.length} exceeds limit of ${VECTORIZATION_CONFIG.MAX_CONTENT_LENGTH}`)
      return {
        success: false,
        message: 'Document content exceeds maximum allowed size',
        error: `Content length ${document.content.length} exceeds limit of ${VECTORIZATION_CONFIG.MAX_CONTENT_LENGTH}`
      }
    }

    console.log(`[DOCUMENT VECTORIZATION] Updating document status to processing...`)
    
    // Update document status to processing
    await supabase
      .from('documents')
      .update({ status: 'processing' })
      .eq('id', documentId)

    // Use provided options or defaults
    const chunkSize = options?.chunkSize || VECTORIZATION_CONFIG.DEFAULT_CHUNK_SIZE
    const chunkOverlap = options?.chunkOverlap || VECTORIZATION_CONFIG.DEFAULT_CHUNK_OVERLAP
    const maxChunks = options?.maxChunks || VECTORIZATION_CONFIG.MAX_CHUNKS_PER_DOCUMENT
    const batchSize = options?.batchSize || VECTORIZATION_CONFIG.BATCH_SIZE

    console.log(`[DOCUMENT VECTORIZATION] Configuration:`, {
      chunkSize,
      chunkOverlap,
      maxChunks,
      batchSize,
      contentLength: document.content.length
    })

    // Create text splitter with optimized settings
    console.log(`[DOCUMENT VECTORIZATION] Creating text splitter...`)
    const textSplitter = new RecursiveCharacterTextSplitter({
      chunkSize,
      chunkOverlap,
      separators: ['\n\n', '\n', ' ', '']
    })

    // Split document into chunks
    console.log(`[DOCUMENT VECTORIZATION] Splitting document into chunks...`)
    const docs = await textSplitter.createDocuments([document.content], [{
      document_id: documentId,
      user_id: userId,
      thread_id: document.thread_id || null,
      title: document.title,
      file_name: document.file_name,
      file_type: document.file_type
    }])

    console.log(`[DOCUMENT VECTORIZATION] Document split into ${docs.length} chunks`)

    // Limit chunks if necessary
    const limitedDocs = docs.slice(0, maxChunks)
    const totalChunks = docs.length
    const processedChunks = limitedDocs.length

    if (totalChunks > maxChunks) {
      console.warn(`[DOCUMENT VECTORIZATION] Document ${documentId} truncated from ${totalChunks} to ${maxChunks} chunks`)
    }

    console.log(`[DOCUMENT VECTORIZATION] Processing ${processedChunks} chunks (${totalChunks} total)`)

    // Process embeddings in batches to respect API limits
    console.log(`[DOCUMENT VECTORIZATION] Starting embedding generation in batches of ${VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE}...`)
    
    const embeddingsList: number[][] = []
    const totalBatches = Math.ceil(limitedDocs.length / VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE)
    
    for (let i = 0; i < limitedDocs.length; i += VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE) {
      const batchNumber = Math.floor(i / VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE) + 1
      const batch = limitedDocs.slice(i, i + VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE)
      const texts = batch.map(doc => doc.pageContent)
      
      console.log(`[DOCUMENT VECTORIZATION] Processing embedding batch ${batchNumber}/${totalBatches} (${batch.length} chunks)`)
      
      try {
        const batchStartTime = Date.now()
        const batchEmbeddings = await embeddings.embedDocuments(texts)
        const batchEndTime = Date.now()
        
        embeddingsList.push(...batchEmbeddings)
        
        console.log(`[DOCUMENT VECTORIZATION] Batch ${batchNumber} completed in ${batchEndTime - batchStartTime}ms`)
        
        // Rate limiting delay between batches
        if (i + VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE < limitedDocs.length) {
          console.log(`[DOCUMENT VECTORIZATION] Waiting ${VECTORIZATION_CONFIG.RATE_LIMIT_DELAY}ms before next batch...`)
          await new Promise(resolve => setTimeout(resolve, VECTORIZATION_CONFIG.RATE_LIMIT_DELAY))
        }
      } catch (embeddingError) {
        console.error(`[DOCUMENT VECTORIZATION] Embedding batch ${batchNumber} error:`, embeddingError)
        throw new Error(`Failed to generate embeddings for batch ${batchNumber}`)
      }
    }

    console.log(`[DOCUMENT VECTORIZATION] All embeddings generated successfully (${embeddingsList.length} total)`)

    // Prepare vector chunks for batch insertion
    console.log(`[DOCUMENT VECTORIZATION] Preparing vector chunks for database insertion...`)
    
    const vectorChunks = limitedDocs.map((doc, index) => ({
      document_id: documentId,
      user_id: userId,
      thread_id: document.thread_id || null,
      content: doc.pageContent,
      embedding: embeddingsList[index],
      metadata: {
        ...doc.metadata,
        chunk_index: index,
        chunk_size: doc.pageContent.length,
        document_title: document.title,
        file_name: document.file_name,
        file_type: document.file_type,
        processing_timestamp: new Date().toISOString(),
        total_chunks: totalChunks,
        processed_chunks: processedChunks
      },
      chunk_index: index
    }))

    console.log(`[DOCUMENT VECTORIZATION] Prepared ${vectorChunks.length} vector chunks for insertion`)

    // Insert vector chunks in batches
    console.log(`[DOCUMENT VECTORIZATION] Starting database insertion in batches of ${batchSize}...`)
    
    let insertedCount = 0
    const totalInsertBatches = Math.ceil(vectorChunks.length / batchSize)
    
    for (let i = 0; i < vectorChunks.length; i += batchSize) {
      const batchNumber = Math.floor(i / batchSize) + 1
      const batch = vectorChunks.slice(i, i + batchSize)
      
      console.log(`[DOCUMENT VECTORIZATION] Inserting batch ${batchNumber}/${totalInsertBatches} (${batch.length} chunks)`)
      
      try {
        const insertStartTime = Date.now()
        const { error: insertError } = await supabase
          .from('vector_chunks')
          .insert(batch)

        if (insertError) {
          throw new Error(`Batch insertion failed: ${insertError.message}`)
        }

        const insertEndTime = Date.now()
        insertedCount += batch.length
        
        console.log(`[DOCUMENT VECTORIZATION] Batch ${batchNumber} inserted successfully in ${insertEndTime - insertStartTime}ms (${insertedCount}/${vectorChunks.length} total)`)
        
        // Small delay between batches to prevent overwhelming the database
        if (i + batchSize < vectorChunks.length) {
          console.log(`[DOCUMENT VECTORIZATION] Waiting 100ms before next insertion batch...`)
          await new Promise(resolve => setTimeout(resolve, 100))
        }
      } catch (batchError) {
        console.error(`[DOCUMENT VECTORIZATION] Batch ${batchNumber} insertion error:`, batchError)
        
        // Update document status to failed
        await supabase
          .from('documents')
          .update({ status: 'failed' })
          .eq('id', documentId)

        return {
          success: false,
          message: 'Failed to store vector chunks in batches',
          error: batchError.message,
          processedChunks: insertedCount,
          totalChunks: vectorChunks.length
        }
      }
    }

    console.log(`[DOCUMENT VECTORIZATION] All vector chunks inserted successfully (${insertedCount} total)`)

    // Update document status to completed
    console.log(`[DOCUMENT VECTORIZATION] Updating document status to completed...`)
    
    await supabase
      .from('documents')
      .update({ 
        status: 'completed',
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId)

    const endTime = Date.now()
    const totalTime = endTime - startTime
    
    console.log(`[DOCUMENT VECTORIZATION] ✅ Document vectorization completed successfully!`)
    console.log(`[DOCUMENT VECTORIZATION] 📊 Summary:`, {
      documentId,
      userId,
      totalTime: `${totalTime}ms`,
      processedChunks,
      totalChunks,
      insertedCount,
      averageTimePerChunk: `${Math.round(totalTime / processedChunks)}ms`
    })

    return {
      success: true,
      message: `Successfully vectorized document into ${processedChunks} chunks (${insertedCount} inserted)`,
      vectorCount: insertedCount,
      processedChunks,
      totalChunks
    }

  } catch (error) {
    const endTime = Date.now()
    const totalTime = endTime - startTime
    
    console.error(`[DOCUMENT VECTORIZATION] ❌ Document vectorization failed after ${totalTime}ms:`, error)
    
    // Update document status to failed
    await supabase
      .from('documents')
      .update({ status: 'failed' })
      .eq('id', documentId)

    return {
      success: false,
      message: 'Document vectorization failed',
      error: error.message
    }
  }
}

/**
 * Utility function to process embeddings in batches with rate limiting
 */
async function processEmbeddingsInBatches(
  texts: string[],
  batchSize: number = VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE
): Promise<number[][]> {
  console.log(`[EMBEDDING BATCHES] Starting batch processing for ${texts.length} texts in batches of ${batchSize}`)
  
  const embeddingsList: number[][] = []
  const totalBatches = Math.ceil(texts.length / batchSize)
  
  for (let i = 0; i < texts.length; i += batchSize) {
    const batchNumber = Math.floor(i / batchSize) + 1
    const batch = texts.slice(i, i + batchSize)
    
    console.log(`[EMBEDDING BATCHES] Processing batch ${batchNumber}/${totalBatches} (${batch.length} texts)`)
    
    try {
      const batchStartTime = Date.now()
      const batchEmbeddings = await embeddings.embedDocuments(batch)
      const batchEndTime = Date.now()
      
      embeddingsList.push(...batchEmbeddings)
      
      console.log(`[EMBEDDING BATCHES] Batch ${batchNumber} completed in ${batchEndTime - batchStartTime}ms`)
      
      // Rate limiting delay between batches
      if (i + batchSize < texts.length) {
        console.log(`[EMBEDDING BATCHES] Waiting ${VECTORIZATION_CONFIG.RATE_LIMIT_DELAY}ms before next batch...`)
        await new Promise(resolve => setTimeout(resolve, VECTORIZATION_CONFIG.RATE_LIMIT_DELAY))
      }
    } catch (embeddingError) {
      console.error(`[EMBEDDING BATCHES] Batch ${batchNumber} error:`, embeddingError)
      throw new Error(`Failed to generate embeddings for batch ${batchNumber}`)
    }
  }
  
  console.log(`[EMBEDDING BATCHES] ✅ All batches completed successfully (${embeddingsList.length} embeddings)`)
  return embeddingsList
}

/**
 * Utility function to insert vector chunks in batches
 */
async function insertVectorChunksInBatches(
  vectorChunks: any[],
  batchSize: number = VECTORIZATION_CONFIG.BATCH_SIZE
): Promise<number> {
  console.log(`[DATABASE BATCHES] Starting batch insertion for ${vectorChunks.length} chunks in batches of ${batchSize}`)
  
  let insertedCount = 0
  const totalBatches = Math.ceil(vectorChunks.length / batchSize)
  
  for (let i = 0; i < vectorChunks.length; i += batchSize) {
    const batchNumber = Math.floor(i / batchSize) + 1
    const batch = vectorChunks.slice(i, i + batchSize)
    
    console.log(`[DATABASE BATCHES] Inserting batch ${batchNumber}/${totalBatches} (${batch.length} chunks)`)
    
    try {
      const insertStartTime = Date.now()
      const { error: insertError } = await supabase
        .from('vector_chunks')
        .insert(batch)

      if (insertError) {
        throw new Error(`Batch insertion failed: ${insertError.message}`)
      }

      const insertEndTime = Date.now()
      insertedCount += batch.length
      
      console.log(`[DATABASE BATCHES] Batch ${batchNumber} inserted successfully in ${insertEndTime - insertStartTime}ms (${insertedCount}/${vectorChunks.length} total)`)
      
      // Small delay between batches to prevent overwhelming the database
      if (i + batchSize < vectorChunks.length) {
        console.log(`[DATABASE BATCHES] Waiting 100ms before next batch...`)
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    } catch (batchError) {
      console.error(`[DATABASE BATCHES] Batch ${batchNumber} insertion error:`, batchError)
      throw batchError
    }
  }
  
  console.log(`[DATABASE BATCHES] ✅ All batches inserted successfully (${insertedCount} total)`)
  return insertedCount
}

/**
 * Vectorize chat history for a specific thread with optimization
 */
async function vectorizeChatHistory(
  threadId: string, 
  userId: string,
  options?: VectorizationRequest['options']
): Promise<VectorizationResponse> {
  const startTime = Date.now()
  console.log(`[CHAT HISTORY VECTORIZATION] Starting chat history vectorization for thread ${threadId}, user ${userId}`)
  
  try {
    console.log(`[CHAT HISTORY VECTORIZATION] Fetching chat history from database...`)
    
    // Fetch chat history for the thread
    const { data: conversations, error: convError } = await supabase
      .from('conversations')
      .select('*')
      .eq('thread_id', threadId)
      .eq('user_id', userId)
      .order('created_at', { ascending: true })

    if (convError || !conversations || conversations.length === 0) {
      console.warn(`[CHAT HISTORY VECTORIZATION] No chat history found for thread ${threadId}`)
      return {
        success: false,
        message: 'No chat history found for thread',
        error: convError?.message
      }
    }

    console.log(`[CHAT HISTORY VECTORIZATION] Found ${conversations.length} conversations in thread`)

    // Combine conversations into meaningful chunks
    console.log(`[CHAT HISTORY VECTORIZATION] Creating chat chunks...`)
    const chatChunks = createChatChunks(conversations)

    if (chatChunks.length === 0) {
      console.warn(`[CHAT HISTORY VECTORIZATION] No meaningful chat content to vectorize`)
      return {
        success: false,
        message: 'No meaningful chat content to vectorize',
        error: 'Empty chat chunks'
      }
    }

    console.log(`[CHAT HISTORY VECTORIZATION] Created ${chatChunks.length} chat chunks`)

    // Use provided options or defaults for chat history
    const maxChunks = options?.maxChunks || 200 // Lower limit for chat history
    const batchSize = options?.batchSize || VECTORIZATION_CONFIG.BATCH_SIZE
    const limitedChunks = chatChunks.slice(0, maxChunks)
    const totalChunks = chatChunks.length
    const processedChunks = limitedChunks.length

    if (totalChunks > maxChunks) {
      console.warn(`[CHAT HISTORY VECTORIZATION] Chat history truncated from ${totalChunks} to ${maxChunks} chunks`)
    }

    console.log(`[CHAT HISTORY VECTORIZATION] Processing ${processedChunks} chat chunks (${totalChunks} total)`)

    // Generate embeddings for chat chunks using batch processing
    console.log(`[CHAT HISTORY VECTORIZATION] Starting embedding generation for chat chunks...`)
    const texts = limitedChunks.map(chunk => chunk.content)
    const embeddingsList = await processEmbeddingsInBatches(texts, VECTORIZATION_CONFIG.MAX_EMBEDDING_BATCH_SIZE)

    console.log(`[CHAT HISTORY VECTORIZATION] Generated embeddings for ${embeddingsList.length} chat chunks`)

    // Prepare vector chunks for chat history
    console.log(`[CHAT HISTORY VECTORIZATION] Preparing vector chunks for database insertion...`)
    const vectorChunks = limitedChunks.map((chunk, index) => ({
      document_id: null, // Chat history doesn't have a document_id
      user_id: userId,
      thread_id: threadId,
      content: chunk.content,
      embedding: embeddingsList[index],
      metadata: {
        ...chunk.metadata,
        chunk_index: index,
        chunk_size: chunk.content.length,
        thread_id: threadId,
        is_chat_history: true,
        conversation_count: chunk.metadata.conversation_count,
        date_range: chunk.metadata.date_range,
        processing_timestamp: new Date().toISOString(),
        total_chunks: totalChunks,
        processed_chunks: processedChunks
      },
      chunk_index: index
    }))

    console.log(`[CHAT HISTORY VECTORIZATION] Prepared ${vectorChunks.length} vector chunks for insertion`)

    // Insert chat history vector chunks using batch processing
    console.log(`[CHAT HISTORY VECTORIZATION] Starting database insertion in batches of ${batchSize}...`)
    const insertedCount = await insertVectorChunksInBatches(vectorChunks, batchSize)

    console.log(`[CHAT HISTORY VECTORIZATION] All chat history vector chunks inserted successfully (${insertedCount} total)`)

    const endTime = Date.now()
    const totalTime = endTime - startTime
    
    console.log(`[CHAT HISTORY VECTORIZATION] ✅ Chat history vectorization completed successfully!`)
    console.log(`[CHAT HISTORY VECTORIZATION] 📊 Summary:`, {
      threadId,
      userId,
      totalTime: `${totalTime}ms`,
      conversations: conversations.length,
      processedChunks,
      totalChunks,
      insertedCount,
      averageTimePerChunk: `${Math.round(totalTime / processedChunks)}ms`
    })

    return {
      success: true,
      message: `Successfully vectorized chat history into ${processedChunks} chunks (${insertedCount} inserted)`,
      vectorCount: insertedCount,
      processedChunks,
      totalChunks
    }

  } catch (error) {
    const endTime = Date.now()
    const totalTime = endTime - startTime
    
    console.error(`[CHAT HISTORY VECTORIZATION] ❌ Chat history vectorization failed after ${totalTime}ms:`, error)
    return {
      success: false,
      message: 'Chat history vectorization failed',
      error: error.message
    }
  }
}

/**
 * Create meaningful chunks from chat conversations
 */
function createChatChunks(conversations: any[]): Array<{ content: string, metadata: Record<string, any> }> {
  console.log(`[CHAT CHUNKS] Creating chunks from ${conversations.length} conversations`)
  
  const chunks: Array<{ content: string, metadata: Record<string, any> }> = []
  
  // Group conversations by time proximity (within 1 hour)
  const conversationGroups: any[][] = []
  let currentGroup: any[] = []
  
  for (let i = 0; i < conversations.length; i++) {
    const conv = conversations[i]
    
    if (currentGroup.length === 0) {
      currentGroup.push(conv)
    } else {
      const lastConv = currentGroup[currentGroup.length - 1]
      const timeDiff = new Date(conv.created_at).getTime() - new Date(lastConv.created_at).getTime()
      const oneHour = 60 * 60 * 1000
      
      if (timeDiff <= oneHour) {
        currentGroup.push(conv)
      } else {
        conversationGroups.push([...currentGroup])
        currentGroup = [conv]
      }
    }
  }
  
  if (currentGroup.length > 0) {
    conversationGroups.push(currentGroup)
  }

  console.log(`[CHAT CHUNKS] Grouped conversations into ${conversationGroups.length} time-based groups`)

  // Create chunks from conversation groups
  conversationGroups.forEach((group, groupIndex) => {
    const content = group.map(conv => `${conv.role}: ${conv.content}`).join('\n\n')
    
    if (content.length > 50) { // Only create chunks for meaningful content
      const firstDate = new Date(group[0].created_at)
      const lastDate = new Date(group[group.length - 1].created_at)
      
      chunks.push({
        content,
        metadata: {
          conversation_count: group.length,
          date_range: {
            start: firstDate.toISOString(),
            end: lastDate.toISOString()
          },
          group_index: groupIndex,
          roles: [...new Set(group.map(c => c.role))]
        }
      })
    }
  })

  console.log(`[CHAT CHUNKS] Created ${chunks.length} meaningful chunks from ${conversationGroups.length} groups`)
  return chunks
}

/**
 * Archive thread and vectorize its complete history
 */
async function archiveThread(threadId: string, userId: string): Promise<VectorizationResponse> {
  try {
    // Get thread information
    const { data: thread, error: threadError } = await supabase
      .from('threads')
      .select('*')
      .eq('id', threadId)
      .eq('user_id', userId)
      .single()

    if (threadError || !thread) {
      return {
        success: false,
        message: 'Thread not found or access denied',
        error: threadError?.message
      }
    }

    // Get all conversations for the thread
    const { data: conversations, error: convError } = await supabase
      .from('conversations')
      .select('*')
      .eq('thread_id', threadId)
      .eq('user_id', userId)
      .order('created_at', { ascending: true })

    if (convError) {
      return {
        success: false,
        message: 'Failed to retrieve thread conversations',
        error: convError.message
      }
    }

    // Create comprehensive thread archive
    const archiveContent = createThreadArchive(thread, conversations || [])
    
    // Generate embedding for the archive
    const [archiveEmbedding] = await embeddings.embedDocuments([archiveContent])

    // Store archive in vector_chunks table
    const { error: insertError } = await supabase
      .from('vector_chunks')
      .insert({
        document_id: null,
        user_id: userId,
        content: archiveContent,
        embedding: archiveEmbedding,
        metadata: {
          is_thread_archive: true,
          thread_id: threadId,
          thread_title: thread.title,
          conversation_count: conversations?.length || 0,
          archive_date: new Date().toISOString(),
          date_range: {
            start: thread.created_at,
            end: thread.updated_at
          }
        },
        chunk_index: 0
      })

    if (insertError) {
      return {
        success: false,
        message: 'Failed to store thread archive',
        error: insertError.message
      }
    }

    // Update thread status to archived
    await supabase
      .from('threads')
      .update({ status: 'archived' })
      .eq('id', threadId)

    return {
      success: true,
      message: 'Thread successfully archived and vectorized',
      vectorCount: 1
    }

  } catch (error) {
    console.error('Thread archival error:', error)
    return {
      success: false,
      message: 'Thread archival failed',
      error: error.message
    }
  }
}

/**
 * Create a comprehensive archive of a thread's content
 */
function createThreadArchive(thread: any, conversations: any[]): string {
  const archive = [
    `THREAD ARCHIVE: ${thread.title}`,
    `Created: ${new Date(thread.created_at).toLocaleString()}`,
    `Last Activity: ${new Date(thread.updated_at).toLocaleString()}`,
    `Total Conversations: ${conversations.length}`,
    '',
    'CONVERSATION HISTORY:',
    '===================='
  ]

  conversations.forEach((conv, index) => {
    archive.push(
      `[${index + 1}] ${conv.role.toUpperCase()} (${new Date(conv.created_at).toLocaleString()}):`,
      conv.content,
      ''
    )
  })

  return archive.join('\n')
}

/**
 * Main Edge Function handler
 */
serve(async (req) => {
  const requestStartTime = Date.now()
  console.log(`[EDGE FUNCTION] 🚀 Vectorization request received: ${req.method} ${req.url}`)
  
  // Handle CORS
  if (req.method === 'OPTIONS') {
    console.log(`[EDGE FUNCTION] Handling CORS preflight request`)
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      }
    })
  }

  try {
    console.log(`[EDGE FUNCTION] Verifying authentication...`)
    
    // Verify authentication
    const authHeader = req.headers.get('authorization')
    if (!authHeader) {
      console.error(`[EDGE FUNCTION] ❌ No authorization header provided`)
      return new Response(
        JSON.stringify({ error: 'Authorization header required' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Get user from JWT token
    const { data: { user }, error: authError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''))
    
    if (authError || !user) {
      console.error(`[EDGE FUNCTION] ❌ Authentication failed:`, authError?.message)
      return new Response(
        JSON.stringify({ error: 'Invalid authentication token' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log(`[EDGE FUNCTION] ✅ Authentication successful for user: ${user.id}`)

    // Parse request body
    console.log(`[EDGE FUNCTION] Parsing request body...`)
    const requestData: VectorizationRequest = await req.json()
    
    if (!requestData.type || !requestData.userId) {
      console.error(`[EDGE FUNCTION] ❌ Missing required fields:`, { type: requestData.type, userId: requestData.userId })
      return new Response(
        JSON.stringify({ error: 'Missing required fields: type and userId' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Verify user owns the resource
    if (requestData.userId !== user.id) {
      console.error(`[EDGE FUNCTION] ❌ Unauthorized access: requested user ${requestData.userId} != authenticated user ${user.id}`)
      return new Response(
        JSON.stringify({ error: 'Unauthorized access to resource' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      )
    }

    console.log(`[EDGE FUNCTION] Processing ${requestData.type} vectorization for user ${requestData.userId}`)
    if (requestData.options) {
      console.log(`[EDGE FUNCTION] Custom options provided:`, requestData.options)
    }

    let result: VectorizationResponse

    // Route to appropriate vectorization function with options
    switch (requestData.type) {
      case 'document':
        if (!requestData.documentId) {
          console.error(`[EDGE FUNCTION] ❌ Missing documentId for document vectorization`)
          return new Response(
            JSON.stringify({ error: 'documentId required for document vectorization' }),
            { status: 400, headers: { 'Content-Type': 'application/json' } }
          )
        }
        console.log(`[EDGE FUNCTION] 📄 Starting document vectorization for document ${requestData.documentId}`)
        result = await vectorizeDocument(requestData.documentId, requestData.userId, requestData.options)
        break

      case 'chat_history':
        if (!requestData.threadId) {
          console.error(`[EDGE FUNCTION] ❌ Missing threadId for chat history vectorization`)
          return new Response(
            JSON.stringify({ error: 'threadId required for chat history vectorization' }),
            { status: 400, headers: { 'Content-Type': 'application/json' } }
          )
        }
        console.log(`[EDGE FUNCTION] 💬 Starting chat history vectorization for thread ${requestData.threadId}`)
        result = await vectorizeChatHistory(requestData.threadId, requestData.userId, requestData.options)
        break

      default:
        console.error(`[EDGE FUNCTION] ❌ Invalid vectorization type: ${requestData.type}`)
        return new Response(
          JSON.stringify({ error: 'Invalid vectorization type' }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        )
    }

    const requestEndTime = Date.now()
    const totalRequestTime = requestEndTime - requestStartTime
    
    console.log(`[EDGE FUNCTION] 📊 Request completed in ${totalRequestTime}ms:`, {
      type: requestData.type,
      userId: requestData.userId,
      success: result.success,
      vectorCount: result.vectorCount,
      processedChunks: result.processedChunks,
      totalChunks: result.totalChunks
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
    
    console.error(`[EDGE FUNCTION] ❌ Request failed after ${totalRequestTime}ms:`, error)
    return new Response(
      JSON.stringify({ 
        success: false,
        message: 'Internal server error',
        error: error.message 
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