// Shared authentication module for Edge Functions
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
const supabase = createClient(supabaseUrl, supabaseServiceKey)

// User preferences interface
export interface UserPreferences {
  rag?: {
    default_model?: string
    temperature?: number
    max_tokens?: number
    include_chat_history?: boolean
    cross_thread_search?: boolean
    similarity_threshold?: number
  }
  processing?: {
    chunk_size?: number
    chunk_overlap?: number
    max_chunks_per_document?: number
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

// Auth validation result interface
export interface AuthResult {
  user: any
  preferences: UserPreferences
  error?: string
}

/**
 * Enhanced authentication and user preferences validation
 * This function validates JWT tokens and fetches user preferences
 */
export async function validateAuthAndGetPreferences(authHeader: string): Promise<AuthResult> {
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
        preferences: getDefaultPreferences()
      }
    }

    console.log(`[AUTH] ✅ User preferences loaded successfully`)
    return { user, preferences: preferences || getDefaultPreferences() }

  } catch (error) {
    console.error(`[AUTH] ❌ Authentication validation error:`, error)
    return { user: null, preferences: {}, error: 'Authentication validation failed' }
  }
}

/**
 * Get default user preferences
 */
function getDefaultPreferences(): UserPreferences {
  return {
    rag: {
      default_model: 'gpt-4',
      temperature: 0.7,
      max_tokens: 1000,
      include_chat_history: true,
      cross_thread_search: true,
      similarity_threshold: 0.7
    },
    processing: {
      chunk_size: 1000,
      chunk_overlap: 200,
      max_chunks_per_document: 1000
    },
    ui: {
      theme: 'light',
      compact_mode: false,
      show_sources: true,
      auto_scroll: true
    },
    notifications: {
      email_notifications: false,
      processing_complete: true,
      error_alerts: true
    }
  }
}

/**
 * Validate user ownership of a resource
 */
export function validateUserOwnership(userId: string, resourceUserId: string): boolean {
  return userId === resourceUserId
}

/**
 * Log authentication events for monitoring
 */
export function logAuthEvent(event: string, userId: string, details?: any) {
  console.log(`[AUTH EVENT] ${event} for user ${userId}`, details || '')
}

/**
 * Get user profile information
 */
export async function getUserProfile(userId: string) {
  try {
    const { data: profile, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('user_id', userId)
      .single()

    if (error) {
      console.warn(`[AUTH] Failed to fetch user profile:`, error.message)
      return null
    }

    return profile
  } catch (error) {
    console.error(`[AUTH] Error fetching user profile:`, error)
    return null
  }
}

/**
 * Update user preferences
 */
export async function updateUserPreferences(userId: string, preferences: Partial<UserPreferences>) {
  try {
    const { error } = await supabase
      .rpc('update_user_preferences', { 
        p_user_id: userId, 
        p_preferences: preferences 
      })

    if (error) {
      console.error(`[AUTH] Failed to update user preferences:`, error.message)
      return false
    }

    console.log(`[AUTH] ✅ User preferences updated successfully`)
    return true
  } catch (error) {
    console.error(`[AUTH] Error updating user preferences:`, error)
    return false
  }
} 