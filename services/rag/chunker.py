from __future__ import annotations

import re
from typing import Iterable


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 1800, overlap_chars: int = 200) -> list[str]:
    """Simple dependency-free chunker suitable for MVP RAG ingestion.

    For production, replace with token-aware chunking and semantic splitting.
    """
    text = clean_text(text)
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(para) <= max_chars:
            current = para
        else:
            start = 0
            while start < len(para):
                end = min(start + max_chars, len(para))
                chunks.append(para[start:end])
                start = max(end - overlap_chars, end)
            current = ""
    if current:
        chunks.append(current)

    if overlap_chars > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for prev, chunk in zip(chunks, chunks[1:]):
            prefix = prev[-overlap_chars:]
            overlapped.append(f"{prefix}\n{chunk}")
        chunks = overlapped
    return chunks
