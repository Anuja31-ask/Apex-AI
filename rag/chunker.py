from __future__ import annotations

from dataclasses import dataclass

from .loader import PageText


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    text: str
    page: int
    metadata: dict[str, str | int]


def chunk_pages(pages: list[PageText], max_words: int = 180, overlap_words: int = 30) -> list[TextChunk]:
    if max_words <= overlap_words:
        raise ValueError("max_words must be greater than overlap_words")
    chunks: list[TextChunk] = []
    for page in pages:
        words = page.text.split()
        if not words:
            continue
        step = max_words - overlap_words
        for offset in range(0, len(words), step):
            text = " ".join(words[offset : offset + max_words]).strip()
            if not text:
                continue
            chunk_number = len(chunks)
            chunks.append(
                TextChunk(
                    chunk_id=f"{page.metadata.document_id}-{page.page}-{chunk_number}",
                    text=text,
                    page=page.page,
                    metadata={**page.metadata.as_payload(), "page": page.page},
                )
            )
            if offset + max_words >= len(words):
                break
    return chunks
