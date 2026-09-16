from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth_utils import (
    encode_token,
    hash_password,
    set_session_cookie,
    clear_session_cookie,
    verify_password,
)
from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import AuthCredentials, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    body: AuthCredentials, response: Response, session: Session = Depends(get_db)
) -> User:
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from None
    session.refresh(user)
    set_session_cookie(response, encode_token(user))
    return user


@router.post("/login", response_model=UserOut)
def login(
    body: AuthCredentials, response: Response, session: Session = Depends(get_db)
) -> User:
    user = session.scalar(select(User).where(User.email == body.email.lower()))
    if not verify_password(body.password, user.password_hash if user else None) or user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_session_cookie(response, encode_token(user))
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    clear_session_cookie(response)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
