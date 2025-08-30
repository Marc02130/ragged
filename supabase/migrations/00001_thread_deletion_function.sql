-- Migration: 00001_thread_deletion_function.sql
-- Description: Add stored procedure for cascading thread deletion

-- Create function to delete thread and all associated data
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
    AND (metadata->>'thread_id')::UUID = p_thread_id;

  -- Delete conversations in the thread
  DELETE FROM conversations 
  WHERE thread_id = p_thread_id AND user_id = p_user_id;

  -- Delete documents associated with the thread (if any)
  -- Note: This assumes documents are linked to threads via metadata
  DELETE FROM vector_chunks 
  WHERE user_id = p_user_id 
    AND document_id IN (
      SELECT id FROM documents 
      WHERE user_id = p_user_id 
        AND (metadata->>'thread_id')::UUID = p_thread_id
    );

  DELETE FROM documents 
  WHERE user_id = p_user_id 
    AND (metadata->>'thread_id')::UUID = p_thread_id;

  -- Finally, delete the thread itself
  DELETE FROM threads 
  WHERE id = p_thread_id AND user_id = p_user_id;

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION delete_thread_cascade(UUID, UUID) TO authenticated;

-- Add comment for documentation
COMMENT ON FUNCTION delete_thread_cascade(UUID, UUID) IS 
'Deletes a thread and all associated data (conversations, vector chunks, documents) in a single transaction. Requires user_id verification for security.'; 