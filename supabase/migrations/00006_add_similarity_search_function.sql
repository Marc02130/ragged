-- Create function for vector similarity search to avoid URL length limits
CREATE OR REPLACE FUNCTION search_similar_chunks(
  query_embedding vector(1536),
  p_user_id uuid,
  p_thread_id uuid,
  match_count int DEFAULT 10,
  include_chat_history boolean DEFAULT true
)
RETURNS TABLE (
  content text,
  metadata jsonb,
  embedding vector(1536),
  thread_id uuid,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    vc.content,
    vc.metadata,
    vc.embedding,
    vc.thread_id,
    1 - (vc.embedding <=> query_embedding) as similarity
  FROM vector_chunks vc
  WHERE vc.user_id = p_user_id
    AND vc.thread_id = p_thread_id
    AND (
      include_chat_history = true 
      OR (vc.metadata->>'is_chat_history')::boolean IS NOT TRUE
    )
  ORDER BY vc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;