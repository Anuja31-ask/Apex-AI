from pathlib import Path

from graph.asset_graph import AssetGraph
from rag.pipeline import KnowledgeBase
from rag.unified_context import UnifiedContext
from reports.generator import generate_report


ROOT = Path(__file__).parents[1]
DOCUMENTS = ROOT / "data" / "documents"


def test_unified_context_contains_documents_and_relationships() -> None:
    knowledge_base = KnowledgeBase(DOCUMENTS)
    knowledge_base.ingest()
    result = UnifiedContext(knowledge_base, AssetGraph()).build(
        "Analyze P-101 vibration and identify related assets."
    )

    assert result["authoritative_evidence"] is True
    assert result["sources"]
    assert {item["target"] for item in result["asset_relationships"]} == {"M-101", "S-101", "L-204"}


def test_report_generator_creates_pdf(tmp_path: Path) -> None:
    output = generate_report(
        {
            "asset_id": "P-101",
            "issue": "Abnormal vibration",
            "observed_value": "8.2 mm/s RMS",
            "threshold": "7.1 mm/s RMS",
            "probable_cause": "Bearing degradation",
            "risk": "HIGH",
            "recommendation": "Detailed bearing inspection",
            "approval_status": "REQUIRED",
            "sources": [{"document": "01_P101_Inspection_Report.pdf", "page": 1}],
            "asset_relationships": AssetGraph().relationships("P-101"),
        },
        tmp_path / "APEX_AI_Industrial_Diagnostic_Report.pdf",
    )

    assert output.exists()
    assert output.stat().st_size > 1000