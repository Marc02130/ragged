from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app import db
from app.db import get_db
from app.deps import get_current_user
from app.models import Thread, User
from app.origin import OriginAllowlistMiddleware
from app.routers.auth import router as auth_router
from app.schemas import ThreadCreate, ThreadOut

app = FastAPI(title="RAGged")
app.add_middleware(OriginAllowlistMiddleware)

if settings.cors_origin_list:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

api = APIRouter(prefix="/api")
api.include_router(auth_router)


@api.get("/health")
async def health() -> dict[str, str]:
    """Liveness. async, no I/O — stays green while ingest occupies a worker."""
    return {"status": "ok"}


@api.get("/ready")
def ready() -> dict[str, str]:
    """Readiness. Sync SELECT 1 against Postgres."""
    with db.SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ok"}


@api.post("/threads", response_model=ThreadOut)
def create_thread(
    body: ThreadCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Thread:
    """Slice 3 CSRF target. Slice 4 expands list/archive/restore/delete."""
    thread = Thread(user_id=user.id, title=body.title)
    session.add(thread)
    session.commit()
    session.refresh(thread)
    return thread


app.include_router(api)
