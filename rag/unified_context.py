from __future__ import annotations

from typing import Any

from graph.asset_graph import AssetGraph

from .pipeline import KnowledgeBase


class UnifiedContext:
    """Combine Qdrant evidence and asset-graph relationships for an agent."""

    def __init__(self, knowledge_base: KnowledgeBase, asset_graph: AssetGraph | None = None) -> None:
        self.knowledge_base = knowledge_base
        self.asset_graph = asset_graph or AssetGraph()

    def build(self, question: str, asset_id: str = "P-101", limit: int = 5) -> dict[str, Any]:
        document_result = self.knowledge_base.query(question, limit)
        graph_result = self.asset_graph.summary(asset_id)
        return {
            "query": question,
            "asset_id": graph_result["asset_id"],
            "document_context": document_result["context"],
            "sources": document_result["sources"],
            "asset_relationships": graph_result["relationships"],
            "graph_backend": graph_result["backend"],
            "authoritative_evidence": bool(document_result["sources"]),
        }