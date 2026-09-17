from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.crypto import decrypt_secret, encrypt_secret
from app.models import User, UserLlmSettings

PROVIDERS = ("openai", "xai", "anthropic")
CHAT_MODELS = {
    "openai": settings.OPENAI_CHAT_MODEL,
    "xai": settings.XAI_CHAT_MODEL,
    "anthropic": settings.ANTHROPIC_CHAT_MODEL,
}


def _is_placeholder(key: str) -> bool:
    return (
        not key
        or key in {"sk-not-set", "sk-replace-me"}
        or key.startswith("sk-test")
        or key.startswith("sk-replace")
    )


def get_or_create_settings(session: Session, user: User) -> UserLlmSettings:
    row = session.get(UserLlmSettings, user.id)
    if row is None:
        row = UserLlmSettings(user_id=user.id, chat_provider="openai")
        session.add(row)
        session.flush()
    return row


def configured_map(row: UserLlmSettings | None) -> dict[str, bool]:
    return {
        "openai": bool(row and row.openai_key_enc) or not _is_placeholder(settings.OPENAI_API_KEY),
        "xai": bool(row and row.xai_key_enc) or not _is_placeholder(settings.XAI_API_KEY),
        "anthropic": bool(row and row.anthropic_key_enc)
        or not _is_placeholder(settings.ANTHROPIC_API_KEY),
    }


def resolve_key(row: UserLlmSettings | None, provider: str) -> str | None:
    enc = None
    env = ""
    if provider == "openai":
        enc = row.openai_key_enc if row else None
        env = settings.OPENAI_API_KEY
    elif provider == "xai":
        enc = row.xai_key_enc if row else None
        env = settings.XAI_API_KEY
    elif provider == "anthropic":
        enc = row.anthropic_key_enc if row else None
        env = settings.ANTHROPIC_API_KEY
    if enc:
        plain = decrypt_secret(enc)
        if not _is_placeholder(plain):
            return plain
    if env and not _is_placeholder(env):
        return env
    return None


def apply_update(
    session: Session,
    user: User,
    *,
    openai_api_key: str | None = None,
    xai_api_key: str | None = None,
    anthropic_api_key: str | None = None,
    chat_provider: str | None = None,
) -> UserLlmSettings:
    row = get_or_create_settings(session, user)
    if openai_api_key is not None:
        row.openai_key_enc = encrypt_secret(openai_api_key) if openai_api_key.strip() else None
    if xai_api_key is not None:
        row.xai_key_enc = encrypt_secret(xai_api_key) if xai_api_key.strip() else None
    if anthropic_api_key is not None:
        row.anthropic_key_enc = (
            encrypt_secret(anthropic_api_key) if anthropic_api_key.strip() else None
        )
    if chat_provider is not None:
        if chat_provider not in PROVIDERS:
            raise ValueError("invalid chat_provider")
        row.chat_provider = chat_provider
    flags = configured_map(row)
    if not flags.get(row.chat_provider):
        if chat_provider is not None:
            raise ValueError(f"no API key configured for {chat_provider}")
        for name in PROVIDERS:
            if flags[name]:
                row.chat_provider = name
                break
    row.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(row)
    return row
