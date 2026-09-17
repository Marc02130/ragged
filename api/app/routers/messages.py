from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, get_owned_thread
from app.models import Conversation, Thread, User
from app.schemas import CreateMessageResponse, MessageCreate, MessageOut, SourceOut
from app.services import rag as rag_service

router = APIRouter(tags=["messages"])


def _sources_from_extra(role: str, extra: dict | None) -> list[SourceOut]:
    if role != "assistant" or not extra:
        return []
    raw = extra.get("sources") or []
    return [SourceOut.model_validate(item) for item in raw]


def to_message_out(row: Conversation) -> MessageOut:
    return MessageOut(
        id=row.id,
        role=row.role,
        content=row.content,
        created_at=row.created_at,
        sources=_sources_from_extra(row.role, row.extra),
    )


@router.get("/threads/{thread_id}/messages", response_model=list[MessageOut])
def list_messages(
    thread: Thread = Depends(get_owned_thread),
    session: Session = Depends(get_db),
) -> list[MessageOut]:
    rows = session.scalars(
        select(Conversation)
        .where(Conversation.thread_id == thread.id)
        .order_by(Conversation.created_at)
    ).all()
    return [to_message_out(row) for row in rows]


@router.post("/threads/{thread_id}/messages", response_model=CreateMessageResponse)
def create_message(
    body: MessageCreate,
    user: User = Depends(get_current_user),
    thread: Thread = Depends(get_owned_thread),
    session: Session = Depends(get_db),
) -> CreateMessageResponse:
    user_row, assistant_row = rag_service.answer(session, user, thread.id, body.content)
    return CreateMessageResponse(
        user_message=to_message_out(user_row),
        assistant_message=to_message_out(assistant_row),
    )
