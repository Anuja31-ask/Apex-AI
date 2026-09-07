# APEX-AI Member 4 Workbench

Member 4 owns the trusted knowledge layer, mock internal data adapters, and
report/integration support for the Pump P-101 demonstration.

## Current status

- Six synthetic PDFs are available in `data/documents/`.
- PDF extraction preserves page numbers and document metadata.
- Local embeddings and trust-aware Qdrant retrieval are implemented.
- Qdrant runs in memory by default, so development does not depend on another
	member's backend or a database credential.
- A standalone FastAPI adapter exposes the retrieval and mock internal APIs.
- A local asset graph fallback and optional Neo4j adapter expose P-101
  relationships.
- Unified analysis context, PDF report generation, and JSONL audit events are
	implemented independently of the AI and team backend.
- A LangGraph planner-to-report workflow is implemented at `POST /analysis/run`.
- Quarantined documents are excluded from authoritative retrieval.
- Focused RAG and API tests pass.

## Install and test

From the repository root:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q testing/test_rag.py testing/test_api.py
```

The first embedding run may download the local `all-MiniLM-L6-v2` model once.
After that, retrieval runs locally. No document text is sent to a cloud AI API.

## Run the standalone API

```powershell
python -m uvicorn backend.main:app --reload
```

Then test:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod -Method Post http://127.0.0.1:8000/query -ContentType 'application/json' -Body '{"query":"What vibration was observed in P-101?"}'
Invoke-RestMethod http://127.0.0.1:8000/internal/assets/P101
Invoke-RestMethod http://127.0.0.1:8000/graph/assets/P101
```

API contract:

- `GET /health`
- `POST /query` with `{ "query": "...", "limit": 5 }`
- `GET /internal/assets/P101`
- `GET /internal/maintenance/P101`
- `GET /internal/sensors/P101`
- `GET /graph/assets/P101`
- `GET /graph/assets/P101/relationships/DRIVEN_BY`
- `POST /analysis/context?asset_id=P101`
- `POST /reports/diagnostic`
- `POST /analysis/run?asset_id=P101`

The internal endpoints contain synthetic, read-only data. They are placeholders
for authorized enterprise adapters and are not MRPL SAP/DCS integrations.

## Qdrant modes

Without `QDRANT_URL`, the API uses in-memory Qdrant and needs no credentials.
For a running local Qdrant service, copy `.env.example` to `.env` and set:

```text
QDRANT_URL=http://localhost:6333
```

The later Neo4j phase will use the reserved `NEO4J_*` variables in `.env`.

To use the graph in Neo4j, start the container, set the `NEO4J_*` variables,
run `python -m graph.seed`, and restart the API. Without those variables, the
same graph queries use the local fallback.

## LangGraph analysis workflow

The current local workflow is:

```text
Planner -> Retrieval -> Evidence Analyst -> Validator
				-> Safety Governor -> Report Preparation
```

Run the complete demonstration without a separate backend or model server:

```powershell
& ".venv/Scripts/python.exe" -m ai.run_demo
```

Or call the API after starting Uvicorn:

```powershell
Invoke-RestMethod -Method Post `
	"http://127.0.0.1:8000/analysis/run?asset_id=P101" `
	-ContentType "application/json" `
	-Body '{"query":"Analyze P-101 vibration and identify related assets."}'
```

The response includes the planner output, findings, evidence validation, safety
decision, agent trace, and report path. The demonstration returns
`HUMAN_APPROVAL_REQUIRED` because 8.2 mm/s exceeds the 7.1 mm/s demonstration
threshold. It never controls physical equipment.

The current analyst is a deterministic local evidence analyst so the complete
workflow is reliable offline. The Qwen2.5-VL-7B-Instruct adapter can replace
that node after the team supplies the local model path and confirms available
GPU/CPU resources. The validator and safety governor must remain deterministic.

## Coordination needed

You can continue testing now. Ask the backend member to confirm whether their
service will mount this router or call `POST /query`. Ask the AI member to use
the returned `context` and `sources` fields. Ask the security member to provide
the final trust-status values and document IDs; the current adapter accepts
`trusted`, `pending`, and `quarantined` statuses.
