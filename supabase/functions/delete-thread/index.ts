import { serve } from "std/http/server"
import { createClient } from '@supabase/supabase-js'
import { OpenAIEmbeddings } from "langchain/embeddings/openai"

// Types for thread deletion
interface DeleteThreadRequest {
  threadId: string
  userId: string
  confirmDeletion: boolean
}

interface DeleteThreadResponse {
  success: boolean
  message: string
  archivedConversations?: number
  error?: string
}

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
 * Archive thread and its complete conversation history
 */
async function archiveThread(threadId: string, userId: string): Promise<{ success: boolean; archivedConversations?: number; error?: string }> {
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
        error: 'Thread not found or access denied'
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
        error: `Failed to retrieve thread conversations: ${convError.message}`
      }
    }

    if (!conversations || conversations.length === 0) {
      return {
        success: true,
        archivedConversations: 0
      }
    }

    // Create comprehensive thread archive
    const archiveContent = createThreadArchive(thread, conversations)
    
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
          conversation_count: conversations.length,
          archive_date: new Date().toISOString(),
          date_range: {
            start: thread.created_at,
            end: thread.updated_at
          },
          original_thread_status: thread.status
        },
        chunk_index: 0
      })

    if (insertError) {
      return {
        success: false,
        error: `Failed to store thread archive: ${insertError.message}`
      }
    }

    return {
      success: true,
      archivedConversations: conversations.length
    }

  } catch (error) {
    console.error('Thread archival error:', error)
    return {
      success: false,
      error: `Thread archival failed: ${error.message}`
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
    `Thread Status: ${thread.status}`,
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
 * Delete thread and all associated data
 */
async function deleteThread(threadId: string, userId: string): Promise<{ success: boolean; error?: string }> {
  try {
    // Start a transaction to ensure data consistency
    const { error: deleteError } = await supabase.rpc('delete_thread_cascade', {
      p_thread_id: threadId,
      p_user_id: userId
    })

    if (deleteError) {
      return {
        success: false,
        error: `Failed to delete thread: ${deleteError.message}`
      }
    }

    return {
      success: true
    }

  } catch (error) {
    console.error('Thread deletion error:', error)
    return {
      success: false,
      error: `Thread deletion failed: ${error.message}`
    }
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
    const requestData: DeleteThreadRequest = await req.json()
    
    if (!requestData.threadId || !requestData.userId) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: threadId and userId' }),
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
      .select('id, title')
      .eq('id', requestData.threadId)
      .eq('user_id', requestData.userId)
      .single()

    if (threadError || !thread) {
      return new Response(
        JSON.stringify({ error: 'Thread not found or access denied' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Check if deletion is confirmed
    if (!requestData.confirmDeletion) {
      return new Response(
        JSON.stringify({ 
          success: false,
          message: 'Deletion not confirmed. Set confirmDeletion to true to proceed.',
          threadTitle: thread.title
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Archive thread before deletion
    const archiveResult = await archiveThread(requestData.threadId, requestData.userId)
    
    if (!archiveResult.success) {
      return new Response(
        JSON.stringify({
          success: false,
          message: 'Failed to archive thread before deletion',
          error: archiveResult.error
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Delete the thread and all associated data
    const deleteResult = await deleteThread(requestData.threadId, requestData.userId)
    
    if (!deleteResult.success) {
      return new Response(
        JSON.stringify({
          success: false,
          message: 'Failed to delete thread',
          error: deleteResult.error
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    }

    const response: DeleteThreadResponse = {
      success: true,
      message: `Thread "${thread.title}" successfully deleted and archived`,
      archivedConversations: archiveResult.archivedConversations
    }

    return new Response(
      JSON.stringify(response),
      { 
        status: 200,
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