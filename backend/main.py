from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from integration.mock_internal_api import get_asset, get_maintenance, get_sensor
from graph.asset_graph import AssetGraph
from rag.pipeline import KnowledgeBase


app = FastAPI(title="APEX-AI Member 4 Services", version="0.1.0")
_documents_dir = Path(__file__).parents[1] / "data" / "documents"
_knowledge_base: KnowledgeBase | None = None
_asset_graph = AssetGraph()


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    context: list[str]
    sources: list[dict]


def knowledge_base() -> KnowledgeBase:
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase(_documents_dir)
        _knowledge_base.ingest()
    return _knowledge_base


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "member4-rag"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    result = knowledge_base().query(request.query, request.limit)
    if not result["sources"]:
        raise HTTPException(status_code=404, detail="No trusted evidence found")
    return QueryResponse(**result)


@app.get("/internal/assets/{asset_id}")
def asset(asset_id: str) -> dict:
    return get_asset(asset_id)


@app.get("/internal/maintenance/{asset_id}")
def maintenance(asset_id: str) -> dict:
    return get_maintenance(asset_id)


@app.get("/internal/sensors/{asset_id}")
def sensor(asset_id: str) -> dict:
    return get_sensor(asset_id)


@app.get("/graph/assets/{asset_id}")
def graph_asset(asset_id: str) -> dict:
    return _asset_graph.summary(asset_id)


@app.get("/graph/assets/{asset_id}/relationships/{relationship}")
def graph_relationship(asset_id: str, relationship: str) -> dict:
    return {
        "asset_id": asset_id,
        "relationship": relationship.upper(),
        "results": _asset_graph.related(asset_id, relationship),
    }
