from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user, get_owned_thread
from app.models import Thread, User
from app.schemas import ThreadCreate, ThreadOut

router = APIRouter(prefix="/threads", tags=["threads"])


def _upload_dir(user_id: UUID, thread_id: UUID) -> Path:
    return Path(settings.UPLOAD_ROOT) / str(user_id) / str(thread_id)


@router.get("", response_model=list[ThreadOut])
def list_threads(
    include_archived: bool = False,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[Thread]:
    query = select(Thread).where(Thread.user_id == user.id)
    if not include_archived:
        query = query.where(Thread.status == "active")
    query = query.order_by(Thread.last_activity_at.desc())
    return list(session.scalars(query))


@router.post("", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
def create_thread(
    body: ThreadCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Thread:
    thread = Thread(user_id=user.id, title=body.title)
    session.add(thread)
    session.commit()
    session.refresh(thread)
    return thread


@router.post("/{thread_id}/archive", response_model=ThreadOut)
def archive_thread(
    thread: Thread = Depends(get_owned_thread),
    session: Session = Depends(get_db),
) -> Thread:
    thread.status = "archived"
    session.commit()
    session.refresh(thread)
    return thread


@router.post("/{thread_id}/restore", response_model=ThreadOut)
def restore_thread(
    thread: Thread = Depends(get_owned_thread),
    session: Session = Depends(get_db),
) -> Thread:
    thread.status = "active"
    session.commit()
    session.refresh(thread)
    return thread


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread: Thread = Depends(get_owned_thread),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Response:
    thread_id = thread.id
    user_id = user.id
    session.delete(thread)
    session.commit()
    path = _upload_dir(user_id, thread_id)
    if path.exists():
        shutil.rmtree(path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
