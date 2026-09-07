from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from integration.mock_internal_api import get_asset, get_maintenance, get_sensor
from integration.audit import record_event
from graph.asset_graph import AssetGraph
from rag.pipeline import KnowledgeBase
from rag.unified_context import UnifiedContext
from ai.workflow import build_workflow


app = FastAPI(title="APEX-AI Member 4 Services", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_documents_dir = Path(__file__).parents[1] / "data" / "documents"
_knowledge_base: KnowledgeBase | None = None
_asset_graph = AssetGraph()
_approval_requests: dict[str, dict] = {}
_upload_dir = Path(__file__).parents[1] / "data" / "uploads"


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


@app.post("/auth/demo-login")
def demo_login(username: str = Form(...), password: str = Form(...), role: str = Form("Engineer")) -> dict:
    if not username or not password:
        raise HTTPException(status_code=401, detail="Username and password are required")
    if role not in {"Admin", "Engineer", "Operator", "Viewer"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    record_event("LOGIN", username=username, role=role)
    return {"token": f"demo-{uuid4()}", "username": username, "role": role}


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("Synthetic demonstration"),
    version: str = Form("1.0"),
    classification: str = Form("Internal"),
) -> dict:
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx"}
    filename = Path(file.filename or "document").name
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=415, detail="Unsupported document type")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty document")
    digest = sha256(content).hexdigest()
    _upload_dir.mkdir(parents=True, exist_ok=True)
    (_upload_dir / filename).write_bytes(content)
    document_id = f"UPLOAD-{digest[:12].upper()}"
    record_event("DOCUMENT_UPLOADED", document_id=document_id, filename=filename, sha256=digest)
    return {
        "document_id": document_id,
        "filename": filename,
        "sha256": digest,
        "source": source,
        "version": version,
        "classification": classification,
        "trust_score": 94,
        "trust_status": "trusted",
        "knowledge_base_status": "pending_approval",
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    result = knowledge_base().query(request.query, request.limit)
    record_event("RAG_QUERY", query=request.query, source_count=len(result["sources"]))
    for source in result["sources"]:
        record_event("DOCUMENT_RETRIEVED", document=source["document"], page=source["page"])
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
    result = _asset_graph.summary(asset_id)
    record_event("GRAPH_QUERY", asset_id=result["asset_id"], relationship_count=result["relationship_count"])
    return result


@app.get("/graph/assets/{asset_id}/relationships/{relationship}")
def graph_relationship(asset_id: str, relationship: str) -> dict:
    result = {
        "asset_id": asset_id,
        "relationship": relationship.upper(),
        "results": _asset_graph.related(asset_id, relationship),
    }
    record_event("GRAPH_QUERY", asset_id=asset_id, relationship=relationship.upper())
    return result


@app.post("/analysis/context")
def analysis_context(request: QueryRequest, asset_id: str = "P-101") -> dict:
    result = UnifiedContext(knowledge_base(), _asset_graph).build(request.query, asset_id, request.limit)
    record_event("AGENT_CONTEXT_CREATED", asset_id=result["asset_id"], source_count=len(result["sources"]))
    return result


@app.post("/reports/diagnostic")
def diagnostic_report(result: dict) -> FileResponse:
    from reports.generator import generate_report

    output_path = Path(__file__).parents[1] / "reports" / "generated" / "APEX_AI_Industrial_Diagnostic_Report.pdf"
    generate_report(result, output_path)
    record_event("REPORT_GENERATED", path=str(output_path), asset_id=result.get("asset_id", "P-101"))
    return FileResponse(output_path, media_type="application/pdf", filename=output_path.name)


@app.get("/reports/download")
def download_report() -> FileResponse:
    output_path = Path(__file__).parents[1] / "reports" / "generated" / "APEX_AI_Industrial_Diagnostic_Report.pdf"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Generate a report first")
    return FileResponse(output_path, media_type="application/pdf", filename=output_path.name)


@app.post("/analysis/run")
def analysis_run(request: QueryRequest, asset_id: str = "P-101") -> dict:
    workflow = build_workflow(UnifiedContext(knowledge_base(), _asset_graph))
    result = workflow.invoke({"user_query": request.query, "asset_id": asset_id})
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    report_path = Path(__file__).parents[1] / "reports" / "generated" / "APEX_AI_Industrial_Diagnostic_Report.pdf"
    from reports.generator import generate_report

    generate_report(result["report_payload"], report_path)
    record_event(
        "ANALYSIS_COMPLETED",
        asset_id=result["asset_id"],
        risk=result["risk"],
        approval_status=result["approval_status"],
    )
    return {
        "asset_id": result["asset_id"],
        "plan": result["plan"],
        "findings": result["findings"],
        "validation": result["validation"],
        "risk": result["risk"],
        "approval_status": result["approval_status"],
        "agent_trace": result["agent_trace"],
        "report": str(report_path),
        "model_used": result["model_used"],
        "approval_id": _create_approval(result),
    }


def _create_approval(result: dict) -> str:
    approval_id = f"APR-{uuid4().hex[:10].upper()}"
    _approval_requests[approval_id] = {
        "approval_id": approval_id,
        "asset_id": result["asset_id"],
        "status": "PENDING" if result["approval_status"] == "HUMAN_APPROVAL_REQUIRED" else "NOT_REQUIRED",
        "risk": result["risk"],
    }
    return approval_id


@app.get("/approvals/{approval_id}")
def approval_status(approval_id: str) -> dict:
    if approval_id not in _approval_requests:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return _approval_requests[approval_id]


@app.post("/approvals/{approval_id}/{decision}")
def decide_approval(approval_id: str, decision: str, username: str = "demo-engineer") -> dict:
    if approval_id not in _approval_requests:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Decision must be approve or reject")
    request = _approval_requests[approval_id]
    request.update({"status": "APPROVED" if decision == "approve" else "REJECTED", "decided_by": username})
    record_event("HUMAN_APPROVAL", approval_id=approval_id, decision=decision, username=username)
    return request


app.mount("/app", StaticFiles(directory=Path(__file__).parents[1] / "frontend", html=True), name="frontend")
