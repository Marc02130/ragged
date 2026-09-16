from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth_utils import decode_token
from app.config import settings
from app.db import get_db
from app.models import Thread, User


def get_current_user(request: Request, session: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user_id: uuid.UUID = decode_token(token)
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Not authenticated") from None
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_owned_thread(
    thread_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Thread:
    thread = session.get(Thread, thread_id)
    if thread is None or thread.user_id != user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread
