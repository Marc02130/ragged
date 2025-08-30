-- Migration: 00004_add_user_preferences.sql
-- Description: Add preferences field to user_profiles table for storing user preferences

-- Add preferences column to user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}';

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.preferences IS 'User preferences stored as JSON, including RAG settings, UI preferences, and other user-specific configurations';

-- Create index for preferences queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_preferences ON user_profiles USING GIN (preferences);

-- Update RLS policies to include preferences
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Function to get user preferences with defaults
CREATE OR REPLACE FUNCTION get_user_preferences(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    user_prefs JSONB;
BEGIN
    -- Get user preferences from user_profiles table
    SELECT preferences INTO user_prefs
    FROM user_profiles
    WHERE user_id = p_user_id;
    
    -- Return default preferences if none found
    IF user_prefs IS NULL THEN
        user_prefs := '{
            "rag": {
                "default_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000,
                "include_chat_history": true,
                "cross_thread_search": true,
                "similarity_threshold": 0.7
            },
            "ui": {
                "theme": "light",
                "compact_mode": false,
                "show_sources": true,
                "auto_scroll": true
            },
            "processing": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "max_chunks_per_document": 1000
            },
            "notifications": {
                "email_notifications": false,
                "processing_complete": true,
                "error_alerts": true
            }
        }'::JSONB;
    END IF;
    
    RETURN user_prefs;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_user_preferences(UUID) TO authenticated;

-- Function to update user preferences
CREATE OR REPLACE FUNCTION update_user_preferences(
    p_user_id UUID,
    p_preferences JSONB
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Update or insert user preferences
    INSERT INTO user_profiles (user_id, preferences, updated_at)
    VALUES (p_user_id, p_preferences, NOW())
    ON CONFLICT (user_id)
    DO UPDATE SET 
        preferences = p_preferences,
        updated_at = NOW();
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION update_user_preferences(UUID, JSONB) TO authenticated; 