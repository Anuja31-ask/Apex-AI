from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langgraph.types import Command
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from integration.mock_internal_api import get_asset, get_maintenance, get_sensor
from integration.audit import record_event
from graph.asset_graph import AssetGraph
from rag.pipeline import KnowledgeBase
from rag.unified_context import UnifiedContext
from ai.workflow import build_workflow
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.user import User


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
_upload_dir = Path(__file__).parents[1] / "uploads"


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


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("Synthetic demonstration"),
    version: str = Form("1.0"),
    classification: str = Form("Internal"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if current_user.role.upper() not in {"ADMIN", "ENGINEER"}:
        raise HTTPException(status_code=403, detail="Engineer or Admin role required")
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx"}
    filename = Path(file.filename or "document").name
    if Path(filename).suffix.lower() not in allowed:
        raise HTTPException(status_code=415, detail="Unsupported document type")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty document")
    digest = sha256(content).hexdigest()
    _upload_dir.mkdir(parents=True, exist_ok=True)
    (_upload_dir / filename).write_bytes(content)
    document = Document(
        owner_id=current_user.id,
        original_filename=filename,
        stored_filename=f"{uuid4()}-{filename}",
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        sha256_hash=digest,
        document_type=classification,
        status="trusted",
    )
    db.add(document)
    db.flush()
    db.add(DocumentVersion(
        document_id=document.id,
        version_number=1,
        filename=filename,
        sha256_hash=digest,
        file_size=len(content),
        created_by=current_user.id,
    ))
    db.add(AuditLog(
        user_id=current_user.id,
        action="DOCUMENT_UPLOADED",
        resource_type="document",
        resource_id=str(document.id),
        details={"sha256": digest, "source": source, "version": version},
    ))
    db.commit()
    document_id = str(document.id)
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
def query(request: QueryRequest, current_user: User = Depends(get_current_user)) -> QueryResponse:
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
def analysis_context(request: QueryRequest, asset_id: str = "P-101", current_user: User = Depends(get_current_user)) -> dict:
    result = UnifiedContext(knowledge_base(), _asset_graph).build(request.query, asset_id, request.limit)
    record_event("AGENT_CONTEXT_CREATED", asset_id=result["asset_id"], source_count=len(result["sources"]))
    return result


@app.post("/reports/diagnostic")
def diagnostic_report(result: dict, current_user: User = Depends(get_current_user)) -> FileResponse:
    from reports.generator import generate_report

    output_path = Path(__file__).parents[1] / "reports" / "generated" / "APEX_AI_Industrial_Diagnostic_Report.pdf"
    generate_report(result, output_path)
    record_event("REPORT_GENERATED", path=str(output_path), asset_id=result.get("asset_id", "P-101"))
    return FileResponse(output_path, media_type="application/pdf", filename=output_path.name)


@app.get("/reports/download")
def download_report(current_user: User = Depends(get_current_user)) -> FileResponse:
    output_path = Path(__file__).parents[1] / "reports" / "generated" / "APEX_AI_Industrial_Diagnostic_Report.pdf"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Generate a report first")
    return FileResponse(output_path, media_type="application/pdf", filename=output_path.name)


@app.post("/analysis/run")
def analysis_run(
    request: QueryRequest,
    asset_id: str = "P-101",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    workflow = build_workflow(UnifiedContext(knowledge_base(), _asset_graph))
    thread_id = f"APR-{uuid4().hex[:10].upper()}"
    config = {"configurable": {"thread_id": thread_id}}
    result = workflow.invoke({"user_query": request.query, "asset_id": asset_id}, config=config)
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    interrupt_payload = result.get("__interrupt__")
    if interrupt_payload:
        interrupt_value = interrupt_payload[0].value if hasattr(interrupt_payload[0], "value") else interrupt_payload[0]
        approval_id = _create_approval(
            {"asset_id": asset_id, "risk": "HIGH", "approval_status": "HUMAN_APPROVAL_REQUIRED"},
            current_user,
            db,
            thread_id,
            interrupt_value,
        )
        return {
            "asset_id": asset_id,
            "approval_id": approval_id,
            "thread_id": thread_id,
            "approval_status": "HUMAN_APPROVAL_REQUIRED",
            "interrupt": interrupt_value,
            "agent_trace": result.get("agent_trace", []),
        }
    return _finish_analysis(result, current_user, db)


def _finish_analysis(result: dict, current_user: User, db: Session) -> dict:
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
        "approval_id": result.get("approval_id"),
    }


def _create_approval(
    result: dict,
    current_user: User,
    db: Session,
    thread_id: str,
    interrupt_value: dict,
) -> str:
    approval_id = thread_id
    approval = {
        "approval_id": approval_id,
        "thread_id": thread_id,
        "asset_id": result["asset_id"],
        "status": "PENDING" if result["approval_status"] == "HUMAN_APPROVAL_REQUIRED" else "NOT_REQUIRED",
        "risk": result["risk"],
        "interrupt": interrupt_value,
    }
    db.add(AuditLog(
        user_id=current_user.id,
        action="APPROVAL_REQUESTED",
        resource_type="analysis",
        resource_id=approval_id,
        details=approval,
    ))
    db.commit()
    return approval_id


@app.get("/approvals/{approval_id}")
def approval_status(approval_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    event = db.query(AuditLog).filter(
        AuditLog.resource_id == approval_id,
        AuditLog.action.in_(["APPROVAL_REQUESTED", "HUMAN_APPROVAL"]),
    ).order_by(AuditLog.timestamp.desc()).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return event.details


@app.post("/approvals/{approval_id}/{decision}")
def decide_approval(
    approval_id: str,
    decision: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if current_user.role.upper() not in {"ADMIN", "ENGINEER"}:
        raise HTTPException(status_code=403, detail="Engineer or Admin role required")
    existing = db.query(AuditLog).filter(
        AuditLog.resource_id == approval_id,
        AuditLog.action == "APPROVAL_REQUESTED",
    ).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Decision must be approve or reject")
    result = dict(existing.details or {})
    result.update({"status": "APPROVED" if decision == "approve" else "REJECTED", "decided_by": current_user.username})
    db.add(AuditLog(
        user_id=current_user.id,
        action="HUMAN_APPROVAL",
        resource_type="analysis",
        resource_id=approval_id,
        details=result,
    ))
    db.commit()
    workflow = build_workflow(UnifiedContext(knowledge_base(), _asset_graph))
    resumed = workflow.invoke(
        Command(resume=decision),
        config={"configurable": {"thread_id": result["thread_id"]}},
    )
    return {**result, "workflow": _finish_analysis(resumed, current_user, db)}


_frontend_dir = Path(__file__).parents[2] / "frontend"
if _frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
