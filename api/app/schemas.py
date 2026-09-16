from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuthCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=1024)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    created_at: datetime


class ThreadCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=100)


class ThreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: str
    document_count: int
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    file_name: str
    file_size: int
    file_type: str
    title: str
    status: str
    embedding_model: str | None
    chunk_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
