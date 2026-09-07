from pathlib import Path

from rag.pipeline import KnowledgeBase


DOCUMENTS = Path(__file__).parents[1] / "data" / "documents"


def test_ingestion_preserves_sources_and_pages() -> None:
    knowledge_base = KnowledgeBase(DOCUMENTS)
    assert knowledge_base.ingest() > 0

    result = knowledge_base.query("What is the vibration review threshold for P-101?")

    assert result["context"]
    assert result["sources"]
    assert all(source["page"] >= 1 for source in result["sources"])
    assert all(source["trust_status"] == "trusted" for source in result["sources"])


def test_quarantined_documents_are_excluded() -> None:
    knowledge_base = KnowledgeBase(DOCUMENTS)
    knowledge_base.ingest({"02_P101_Equipment_Manual.pdf": "quarantined"})

    result = knowledge_base.query("What does the equipment manual say about P-101?")

    assert all(source["document"] != "02_P101_Equipment_Manual.pdf" for source in result["sources"])
