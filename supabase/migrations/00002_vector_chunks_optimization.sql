-- Migration: 00002_vector_chunks_optimization.sql
-- Description: Optimize vector_chunks table for large document processing and better RLS scoping

-- Add thread_id column to vector_chunks for better scoping
ALTER TABLE vector_chunks 
ADD COLUMN IF NOT EXISTS thread_id UUID REFERENCES threads(id) ON DELETE CASCADE;

-- Add index for thread_id for better query performance
CREATE INDEX IF NOT EXISTS idx_vector_chunks_thread_id ON vector_chunks(thread_id);

-- Add composite index for user_id and thread_id for efficient filtering
CREATE INDEX IF NOT EXISTS idx_vector_chunks_user_thread ON vector_chunks(user_id, thread_id);

-- Add index for document_id and user_id for document-specific queries
CREATE INDEX IF NOT EXISTS idx_vector_chunks_doc_user ON vector_chunks(document_id, user_id);

-- Add index for metadata JSONB for efficient metadata queries
CREATE INDEX IF NOT EXISTS idx_vector_chunks_metadata ON vector_chunks USING GIN (metadata);

-- Add index for chunk_index for ordered retrieval
CREATE INDEX IF NOT EXISTS idx_vector_chunks_chunk_index ON vector_chunks(chunk_index);

-- Add index for created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_vector_chunks_created_at ON vector_chunks(created_at);

-- Add column for processing status
ALTER TABLE vector_chunks 
ADD COLUMN IF NOT EXISTS processing_status TEXT DEFAULT 'completed' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'));

-- Add column for batch information
ALTER TABLE vector_chunks 
ADD COLUMN IF NOT EXISTS batch_info JSONB DEFAULT '{}';

-- Update RLS policies to include thread_id scoping
DROP POLICY IF EXISTS "Users can view own vector chunks" ON vector_chunks;
CREATE POLICY "Users can view own vector chunks" ON vector_chunks
    FOR SELECT USING (
        auth.uid() = user_id AND 
        (thread_id IS NULL OR thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        ))
    );

DROP POLICY IF EXISTS "Users can insert own vector chunks" ON vector_chunks;
CREATE POLICY "Users can insert own vector chunks" ON vector_chunks
    FOR INSERT WITH CHECK (
        auth.uid() = user_id AND 
        (thread_id IS NULL OR thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        ))
    );

DROP POLICY IF EXISTS "Users can update own vector chunks" ON vector_chunks;
CREATE POLICY "Users can update own vector chunks" ON vector_chunks
    FOR UPDATE USING (
        auth.uid() = user_id AND 
        (thread_id IS NULL OR thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        ))
    );

DROP POLICY IF EXISTS "Users can delete own vector chunks" ON vector_chunks;
CREATE POLICY "Users can delete own vector chunks" ON vector_chunks
    FOR DELETE USING (
        auth.uid() = user_id AND 
        (thread_id IS NULL OR thread_id IN (
            SELECT id FROM threads WHERE user_id = auth.uid()
        ))
    );

-- Add function to clean up orphaned vector chunks
CREATE OR REPLACE FUNCTION cleanup_orphaned_vector_chunks()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete vector chunks where document_id is not null but document doesn't exist
    DELETE FROM vector_chunks 
    WHERE document_id IS NOT NULL 
      AND document_id NOT IN (SELECT id FROM documents);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete vector chunks where thread_id is not null but thread doesn't exist
    DELETE FROM vector_chunks 
    WHERE thread_id IS NOT NULL 
      AND thread_id NOT IN (SELECT id FROM threads);
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add function to get vector chunk statistics per user
CREATE OR REPLACE FUNCTION get_user_vector_stats(user_uuid UUID)
RETURNS TABLE(
    total_chunks BIGINT,
    total_documents BIGINT,
    total_threads BIGINT,
    avg_chunks_per_doc NUMERIC,
    total_size_bytes BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(vc.id)::BIGINT as total_chunks,
        COUNT(DISTINCT vc.document_id)::BIGINT as total_documents,
        COUNT(DISTINCT vc.thread_id)::BIGINT as total_threads,
        ROUND(
            CASE 
                WHEN COUNT(DISTINCT vc.document_id) > 0 
                THEN COUNT(vc.id)::NUMERIC / COUNT(DISTINCT vc.document_id)
                ELSE 0 
            END, 2
        ) as avg_chunks_per_doc,
        COALESCE(SUM(LENGTH(vc.content)), 0)::BIGINT as total_size_bytes
    FROM vector_chunks vc
    WHERE vc.user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add function to get thread-specific vector statistics
CREATE OR REPLACE FUNCTION get_thread_vector_stats(thread_uuid UUID, user_uuid UUID)
RETURNS TABLE(
    thread_chunks BIGINT,
    thread_documents BIGINT,
    thread_size_bytes BIGINT,
    last_updated TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(vc.id)::BIGINT as thread_chunks,
        COUNT(DISTINCT vc.document_id)::BIGINT as thread_documents,
        COALESCE(SUM(LENGTH(vc.content)), 0)::BIGINT as thread_size_bytes,
        MAX(vc.created_at) as last_updated
    FROM vector_chunks vc
    WHERE vc.thread_id = thread_uuid 
      AND vc.user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION cleanup_orphaned_vector_chunks() TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_vector_stats(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_thread_vector_stats(UUID, UUID) TO authenticated;

-- Add comments for documentation
COMMENT ON COLUMN vector_chunks.thread_id IS 'Thread ID for scoping vector chunks to specific conversations';
COMMENT ON COLUMN vector_chunks.processing_status IS 'Status of vector chunk processing (pending, processing, completed, failed)';
COMMENT ON COLUMN vector_chunks.batch_info IS 'JSON metadata about batch processing information';
COMMENT ON FUNCTION cleanup_orphaned_vector_chunks() IS 'Cleans up vector chunks that reference non-existent documents or threads';
COMMENT ON FUNCTION get_user_vector_stats(UUID) IS 'Returns vector chunk statistics for a specific user';
COMMENT ON FUNCTION get_thread_vector_stats(UUID, UUID) IS 'Returns vector chunk statistics for a specific thread and user'; 