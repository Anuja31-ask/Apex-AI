from pathlib import Path

from graph.asset_graph import AssetGraph
from rag.pipeline import KnowledgeBase
from rag.unified_context import UnifiedContext
from langgraph.types import Command

from ai.workflow import build_workflow


ROOT = Path(__file__).parents[1]


def test_langgraph_produces_verified_high_risk_demo_result() -> None:
    knowledge_base = KnowledgeBase(ROOT / "data" / "documents")
    knowledge_base.ingest()
    workflow = build_workflow(UnifiedContext(knowledge_base, AssetGraph()))
    config = {"configurable": {"thread_id": "workflow-test-approval"}}
    paused = workflow.invoke(
        {"user_query": "Analyze P-101 vibration and identify related assets.", "asset_id": "P-101"},
        config=config,
    )

    assert paused["__interrupt__"][0].value["type"] == "human_approval"
    result = workflow.invoke(Command(resume="approve"), config=config)

    assert result["agent_trace"][-2:] == ["Report Preparation", "Report Ready"]
    assert result["agent_trace"].count("Safety Governor") >= 2
    assert result["findings"]["observed_vibration"] == 8.2
    assert result["findings"]["threshold_value"] == 7.1
    assert result["validation"]["numerical_check"] == "PASS"
    assert result["approval_status"] == "APPROVED"
    assert result["report_payload"]["sources"]


def test_langgraph_blocks_untrusted_context() -> None:
    knowledge_base = KnowledgeBase(ROOT / "data" / "documents")
    quarantined = {
        path.name: "quarantined"
        for path in (ROOT / "data" / "documents").glob("*.pdf")
    }
    knowledge_base.ingest(quarantined)
    result = build_workflow(UnifiedContext(knowledge_base, AssetGraph())).invoke(
        {"user_query": "Analyze P-101 inspection findings.", "asset_id": "P-101"},
        config={"configurable": {"thread_id": "workflow-test-blocked"}},
    )

    assert result["error"] == "No trusted evidence is available for this analysis."
    assert result["validation"]["evidence_check"] == "FAIL"
    assert result["approval_status"] == "REVIEW_REQUIRED"