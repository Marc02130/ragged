-- Migration: 00003_fix_schema_consistency.sql
-- Description: Fix schema inconsistencies and add missing fields for proper integration

-- Add missing fields to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS file_path TEXT,
ADD COLUMN IF NOT EXISTS vector_status TEXT DEFAULT 'pending' CHECK (vector_status IN ('pending', 'processing', 'ready', 'error')),
ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0;

-- Add missing fields to threads table
ALTER TABLE threads 
ADD COLUMN IF NOT EXISTS document_count INTEGER DEFAULT 0;

-- Add missing fields to vector_chunks table
ALTER TABLE vector_chunks 
ADD COLUMN IF NOT EXISTS thread_id UUID REFERENCES threads(id) ON DELETE CASCADE;

-- Add missing fields to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS vectorized BOOLEAN DEFAULT FALSE;

-- Create indexes for new fields
CREATE INDEX IF NOT EXISTS idx_documents_thread_id ON documents(thread_id);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_thread_id ON vector_chunks(thread_id);
CREATE INDEX IF NOT EXISTS idx_conversations_vectorized ON conversations(vectorized);

-- Update RLS policies to include thread_id
DROP POLICY IF EXISTS "Users can view own documents" ON documents;
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view own vector chunks" ON vector_chunks;
CREATE POLICY "Users can view own vector chunks" ON vector_chunks
    FOR SELECT USING (auth.uid() = user_id);

-- Add function to update document count on thread
CREATE OR REPLACE FUNCTION update_thread_document_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE threads 
        SET document_count = document_count + 1,
            last_activity_at = NOW(),
            updated_at = NOW()
        WHERE id = NEW.thread_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE threads 
        SET document_count = GREATEST(document_count - 1, 0),
            last_activity_at = NOW(),
            updated_at = NOW()
        WHERE id = OLD.thread_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for document count updates
DROP TRIGGER IF EXISTS trigger_update_thread_document_count ON documents;
CREATE TRIGGER trigger_update_thread_document_count
    AFTER INSERT OR DELETE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_thread_document_count();

-- Add function to update thread activity on conversation
CREATE OR REPLACE FUNCTION update_thread_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE threads 
    SET last_activity_at = NOW(),
        updated_at = NOW()
    WHERE id = NEW.thread_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for thread activity updates
DROP TRIGGER IF EXISTS trigger_update_thread_activity ON conversations;
CREATE TRIGGER trigger_update_thread_activity
    AFTER INSERT ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_thread_activity();

-- Update the delete_thread_cascade function to handle new schema
CREATE OR REPLACE FUNCTION delete_thread_cascade(
  p_thread_id UUID,
  p_user_id UUID
) RETURNS VOID AS $$
BEGIN
  -- Verify thread belongs to user
  IF NOT EXISTS (
    SELECT 1 FROM threads 
    WHERE id = p_thread_id AND user_id = p_user_id
  ) THEN
    RAISE EXCEPTION 'Thread not found or access denied';
  END IF;

  -- Delete vector chunks associated with the thread
  DELETE FROM vector_chunks 
  WHERE user_id = p_user_id 
    AND thread_id = p_thread_id;

  -- Delete conversations in the thread
  DELETE FROM conversations 
  WHERE thread_id = p_thread_id AND user_id = p_user_id;

  -- Delete documents associated with the thread
  DELETE FROM documents 
  WHERE thread_id = p_thread_id AND user_id = p_user_id;

  -- Finally, delete the thread itself
  DELETE FROM threads 
  WHERE id = p_thread_id AND user_id = p_user_id;

END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 