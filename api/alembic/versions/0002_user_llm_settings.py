"""per-user LLM API keys and chat provider

Revision ID: 0002_user_llm_settings
Revises: 0001_initial
"""

from alembic import op

revision = "0002_user_llm_settings"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE user_llm_settings (
          user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
          openai_key_enc TEXT,
          xai_key_enc TEXT,
          anthropic_key_enc TEXT,
          chat_provider TEXT NOT NULL DEFAULT 'openai'
            CHECK (chat_provider IN ('openai', 'xai', 'anthropic')),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_llm_settings")
