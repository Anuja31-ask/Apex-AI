# APEX-AI — Member 4 Phase 1 Knowledge Base Guide

## Goal
Create a small, consistent synthetic knowledge base for the single demo:
Pump P-101 inspection → diagnosis → verified report.

## Tools
- Microsoft Word / Google Docs: optional for editing source documents
- ReportLab-generated PDFs: supplied in this pack
- Python 3.10+
- PyMuPDF (`fitz`) or `pypdf`: PDF text extraction
- Qdrant: vector database
- Sentence-transformers or another locally available embedding model
- FastAPI: expose the RAG endpoint later
- Neo4j: add relationship retrieval after Qdrant is stable
- Git/GitHub: version control

## Step 1 — Copy documents
Put the six PDFs in:
data/documents/

Recommended structure:
data/
  documents/
  demo/
  attacks/

## Step 2 — Verify the PDFs
Extract text from every PDF and confirm:
- P-101 appears where expected
- 8.2 mm/s appears in the inspection report
- 7.1 mm/s appears in the SOP/reference
- M-101 and S-101 appear in relevant documents
- page numbers can be preserved as metadata

## Step 3 — Create metadata
For every document store:
- document_id
- filename
- equipment
- document_type
- revision
- trust_status
- sha256
- page_count

Example:
{
  "document_id": "INS-P101-001",
  "equipment": "P-101",
  "document_type": "inspection",
  "trust_status": "trusted"
}

## Step 4 — Chunk
Start simple:
- chunk by page
- then split long pages into ~500–800 token chunks
- overlap ~50–100 tokens
- preserve document_id and page number on every chunk

Do NOT start with sophisticated GraphRAG.

## Step 5 — Embed
Generate local embeddings and store them in Qdrant.

Each point should contain:
- vector
- chunk text
- document_id
- filename
- page
- equipment
- trust_status

## Step 6 — Retrieval tests
Run these exact queries:
1. What is the vibration review threshold for P-101?
2. What vibration was observed in the P-101 inspection?
3. What maintenance was performed on P-101?
4. Which motor drives P-101?
5. Which sensor monitors P-101?
6. What should happen when vibration exceeds the threshold?
7. What happens if the recommendation is shutdown?

Expected important values:
- observed vibration = 8.2 mm/s
- demonstration threshold = 7.1 mm/s
- motor = M-101
- sensor = S-101

## Step 7 — Evidence format
The retriever should return:
{
  "context": "...",
  "sources": [
    {
      "document": "P101_SOP.pdf",
      "page": 1
    }
  ]
}

Do not return only an answer. Preserve the evidence.

## Step 8 — Trust-aware retrieval
Later, Member 2's TrustGate will provide document trust status.

Rule:
if trust_status != "trusted":
    exclude from authoritative retrieval

This is required for the tampered-document demonstration.

## Step 9 — Neo4j after Qdrant
Create only the minimum graph:
P-101 --driven_by--> M-101
P-101 --monitored_by--> S-101
P-101 --connected_to--> L-204

Qdrant = semantic document facts.
Neo4j = asset relationships.

## Definition of Done
Member 4 Phase 1 is complete when:
[ ] six PDFs exist
[ ] PDFs are internally consistent
[ ] text extraction works
[ ] metadata exists
[ ] chunks are created
[ ] embeddings are created
[ ] Qdrant collection is populated
[ ] retrieval returns correct chunks
[ ] source document + page are returned
[ ] untrusted documents can be excluded
[ ] the pipeline can be called by FastAPI
