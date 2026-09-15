from fastapi import APIRouter, FastAPI

app = FastAPI(title="RAGged")
api = APIRouter(prefix="/api")


@api.get("/health")
async def health() -> dict[str, str]:
    """Liveness. async, no I/O — stays green while ingest occupies a worker."""
    return {"status": "ok"}


app.include_router(api)
