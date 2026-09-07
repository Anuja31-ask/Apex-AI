from __future__ import annotations

from pathlib import Path

from graph.asset_graph import AssetGraph
from rag.pipeline import KnowledgeBase
from rag.unified_context import UnifiedContext
from reports.generator import generate_report

from .workflow import build_workflow


if __name__ == "__main__":
    root = Path(__file__).parents[1]
    knowledge_base = KnowledgeBase(root / "data" / "documents")
    knowledge_base.ingest()
    workflow = build_workflow(UnifiedContext(knowledge_base, AssetGraph()))
    result = workflow.invoke(
        {"user_query": "Analyze P-101 vibration and identify related assets.", "asset_id": "P-101"}
    )
    report_path = generate_report(
        result["report_payload"], root / "reports" / "generated" / "APEX_AI_Industrial_Diagnostic_Report.pdf"
    )
    print({"trace": result["agent_trace"], "report": str(report_path), "approval": result["approval_status"]})