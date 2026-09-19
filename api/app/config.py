from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    DATABASE_URL: str
    JWT_SECRET: str = "dev-only-change-me-32-bytes-min!!"
    JWT_TTL_SECONDS: int = 604800
    COOKIE_NAME: str = "ragged_session"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_PATH: str = "/"
    PUBLIC_ORIGINS: str = "http://localhost:8080,http://localhost:3000"
    CORS_ORIGINS: str = ""
    OPENAI_API_KEY: str = "sk-not-set"
    XAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    XAI_CHAT_MODEL: str = "grok-4.5"
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    ANTHROPIC_CHAT_MODEL: str = "claude-sonnet-4-5"
    ANTHROPIC_API_URL: str = "https://api.anthropic.com/v1/messages"
    ANTHROPIC_VERSION: str = "2023-06-01"
    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TIMEOUT_SECONDS: int = 60
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_PER_DOCUMENT: int = 1000
    MAX_CONTENT_CHARS: int = 1_000_000
    MAX_QUERY_CHARS: int = 8000
    SIMILARITY_THRESHOLD: float = 0.4
    RELATIVE_SCORE_MARGIN: float = 0.15
    WIDE_VECTOR_RESULTS: int = 32
    MAX_VECTOR_RESULTS: int = 8
    MAX_FILE_SIZE: int = 10_485_760
    MAX_FILES_PER_THREAD: int = 20
    MAX_TOTAL_SIZE_PER_THREAD: int = 52_428_800
    MAX_TOTAL_SIZE_PER_USER: int = 1_073_741_824
    MAX_UPLOAD_BODY_BYTES: int = 57_671_680
    UPLOAD_ROOT: str = "/data/uploads"
    BCRYPT_ROUNDS: int = 12
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5

    @model_validator(mode="after")
    def reject_wildcard_origins(self) -> "Settings":
        public = [o.strip() for o in self.PUBLIC_ORIGINS.split(",") if o.strip()]
        if not public or "*" in public:
            raise ValueError("PUBLIC_ORIGINS must be a non-empty allowlist without *")
        cors = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if "*" in cors:
            raise ValueError("CORS_ORIGINS must not contain *")
        if len(self.JWT_SECRET) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return self

    @property
    def public_origin_list(self) -> list[str]:
        return [o.strip() for o in self.PUBLIC_ORIGINS.split(",") if o.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
