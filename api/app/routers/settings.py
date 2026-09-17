from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LlmProviderStatus, LlmSettingsOut, LlmSettingsUpdate
from app.services import llm_keys

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_out(row, flags: dict[str, bool]) -> LlmSettingsOut:
    return LlmSettingsOut(
        openai=LlmProviderStatus(configured=flags["openai"]),
        xai=LlmProviderStatus(configured=flags["xai"]),
        anthropic=LlmProviderStatus(configured=flags["anthropic"]),
        chat_provider=row.chat_provider if row else "openai",
        chat_models=dict(llm_keys.CHAT_MODELS),
    )


@router.get("/llm", response_model=LlmSettingsOut)
def get_llm_settings(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> LlmSettingsOut:
    row = llm_keys.get_or_create_settings(session, user)
    session.commit()
    return _to_out(row, llm_keys.configured_map(row))


@router.put("/llm", response_model=LlmSettingsOut)
def put_llm_settings(
    body: LlmSettingsUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> LlmSettingsOut:
    try:
        row = llm_keys.apply_update(
            session,
            user,
            openai_api_key=body.openai_api_key,
            xai_api_key=body.xai_api_key,
            anthropic_api_key=body.anthropic_api_key,
            chat_provider=body.chat_provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _to_out(row, llm_keys.configured_map(row))
