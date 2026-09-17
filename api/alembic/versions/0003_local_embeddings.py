"""local MiniLM embeddings: vector(384)

Revision ID: 0003_local_embeddings
Revises: 0002_user_llm_settings
"""

from alembic import op

revision = "0003_local_embeddings"
down_revision = "0002_user_llm_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM vector_chunks")
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
    op.execute("ALTER TABLE vector_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE vector_chunks ADD COLUMN embedding vector(384) NOT NULL")
    op.execute(
        "CREATE INDEX idx_chunks_embedding ON vector_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        """
        UPDATE documents
        SET embedding_model = 'sentence-transformers/all-MiniLM-L6-v2',
            status = 'failed',
            chunk_count = 0,
            error_message = 'Re-upload required after switching to local embeddings'
        WHERE status = 'ready'
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM vector_chunks")
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
    op.execute("ALTER TABLE vector_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE vector_chunks ADD COLUMN embedding vector(1536) NOT NULL")
    op.execute(
        "CREATE INDEX idx_chunks_embedding ON vector_chunks USING hnsw (embedding vector_cosine_ops)"
    )
