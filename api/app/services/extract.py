from __future__ import annotations

import io
import zipfile

KIND_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "rtf": "application/rtf",
    "txt": "text/plain",
}


class UnsupportedFileType(ValueError):
    pass


def detect_kind(data: bytes) -> str:
    if data.startswith(b"%PDF"):
        return "pdf"
    if data.startswith(b"{\\rtf"):
        return "rtf"
    if data.startswith(b"PK\x03\x04") and _zip_has_word_document(data):
        return "docx"
    if _looks_like_text(data):
        return "txt"
    raise UnsupportedFileType("Unsupported file type")


def extract_text(data: bytes, kind: str) -> str:
    if kind == "pdf":
        return _extract_pdf(data)
    if kind == "docx":
        return _extract_docx(data)
    if kind == "rtf":
        from striprtf.striprtf import rtf_to_text

        return rtf_to_text(data.decode("latin-1", errors="replace"))
    if kind == "txt":
        return _decode_text(data)
    raise UnsupportedFileType("Unsupported file type")


def _zip_has_word_document(data: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return "word/document.xml" in zf.namelist()
    except zipfile.BadZipFile:
        return False


def _looks_like_text(data: bytes) -> bool:
    if not data:
        return False
    if data.count(b"\x00") / len(data) > 0.01:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        try:
            data.decode("cp1252")
            return True
        except UnicodeDecodeError:
            return False


def _decode_text(data: bytes) -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts).strip()


def _extract_docx(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs).strip()
