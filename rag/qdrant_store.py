from __future__ import annotations

import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from .chunker import TextChunk
from .embeddings import LocalEmbedder


class QdrantStore:
    def __init__(self, collection_name: str = "apex_documents", embedder: LocalEmbedder | None = None) -> None:
        url = os.getenv("QDRANT_URL")
        self.client = QdrantClient(url=url) if url else QdrantClient(":memory:")
        self.collection_name = collection_name
        self.embedder = embedder or LocalEmbedder()
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=self.embedder.dimension, distance=models.Distance.COSINE),
            )

    def upsert(self, chunks: list[TextChunk]) -> None:
        if not chunks:
            return
        vectors = self.embedder.encode([chunk.text for chunk in chunks])
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(id=index, vector=vector, payload={"text": chunk.text, **chunk.metadata})
                for index, (chunk, vector) in enumerate(zip(chunks, vectors))
            ],
        )

    def search(self, query: str, limit: int = 5, trusted_only: bool = True) -> list[dict[str, Any]]:
        query_vector = self.embedder.encode([query])[0]
        query_filter = None
        if trusted_only:
            query_filter = models.Filter(
                must=[models.FieldCondition(key="trust_status", match=models.MatchValue(value="trusted"))]
            )
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return [{"score": hit.score, **(hit.payload or {})} for hit in response.points]
