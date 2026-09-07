from pathlib import Path

from .pipeline import KnowledgeBase


if __name__ == "__main__":
    documents = Path(__file__).parents[1] / "data" / "documents"
    knowledge_base = KnowledgeBase(documents)
    count = knowledge_base.ingest()
    print(f"Ingested {count} trusted chunks from {documents}")
    for question in (
        "What is the vibration review threshold for P-101?",
        "What vibration was observed in the P-101 inspection?",
        "What maintenance was performed on P-101?",
    ):
        print(f"\nQUESTION: {question}")
        print(knowledge_base.query(question, limit=3))
