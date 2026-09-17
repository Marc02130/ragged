from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from app.config import settings

FILE_PATH_RE = re.compile(
    r"^[0-9a-f-]{36}/[0-9a-f-]{36}/[0-9a-f-]{36}\.(pdf|docx|txt|rtf)$"
)

EXT_FOR_KIND = {"pdf": ".pdf", "docx": ".docx", "rtf": ".rtf", "txt": ".txt"}


def display_name(filename: str | None) -> str:
    name = os.path.basename(filename or "upload")
    return name or "upload"


def new_relative_path(user_id: uuid.UUID, thread_id: uuid.UUID, kind: str) -> str:
    ext = EXT_FOR_KIND[kind]
    relative = f"{user_id}/{thread_id}/{uuid.uuid4()}{ext}"
    if not FILE_PATH_RE.match(relative):
        raise ValueError("generated path failed validation")
    return relative


def resolve_under_root(relative: str) -> Path:
    root = Path(settings.UPLOAD_ROOT).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("path escapes upload root")
    return path


def write_bytes(relative: str, data: bytes) -> Path:
    path = resolve_under_root(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def unlink_if_exists(relative: str) -> None:
    path = resolve_under_root(relative)
    if path.is_file():
        path.unlink()
