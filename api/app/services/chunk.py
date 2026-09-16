from __future__ import annotations

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def split_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    separators: list[str] | None = None,
) -> list[str]:
    separators = separators if separators is not None else DEFAULT_SEPARATORS
    text = text.strip()
    if not text:
        return []
    chunks = _split(text, chunk_size, separators)
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    merged: list[str] = []
    for chunk in chunks:
        if not merged:
            merged.append(chunk)
            continue
        prev = merged[-1]
        prefix = prev[-overlap:] if len(prev) > overlap else prev
        combined = prefix + chunk if not chunk.startswith(prefix) else chunk
        if len(combined) <= chunk_size + overlap:
            merged.append(combined)
        else:
            merged.append(chunk)
    return merged


def _split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    sep, rest = separators[0], separators[1:]
    if sep == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    pieces = text.split(sep)
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = piece if current == "" else current + sep + piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.extend(_split(current, chunk_size, rest))
        current = piece
    if current:
        chunks.extend(_split(current, chunk_size, rest))
    return [c for c in chunks if c]
