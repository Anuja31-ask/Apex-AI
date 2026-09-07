from __future__ import annotations

from pathlib import Path
from typing import Any

from .chunker import chunk_pages
from .loader import load_directory
from .qdrant_store import QdrantStore


class KnowledgeBase:
    def __init__(self, documents_dir: Path, store: QdrantStore | None = None) -> None:
        self.documents_dir = documents_dir
        self.store = store or QdrantStore()

    def ingest(self, trust_statuses: dict[str, str] | None = None) -> int:
        pages = load_directory(self.documents_dir, trust_statuses)
        chunks = chunk_pages(pages)
        self.store.upsert(chunks)
        return len(chunks)

    def query(self, question: str, limit: int = 5) -> dict[str, Any]:
        results = self.store.search(question, limit=limit, trusted_only=True)
        return {
            "context": [result["text"] for result in results],
            "sources": [
                {
                    "document": result["filename"],
                    "page": result["page"],
                    "document_id": result["document_id"],
                    "trust_status": result["trust_status"],
                    "score": result["score"],
                }
                for result in results
            ],
        }
