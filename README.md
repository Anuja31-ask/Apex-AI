# APEX-AI Member 4 Workbench

## RefineShield integration

The real RefineShield FastAPI application is in `app/main.py`. It keeps the
JWT/database authentication routes under `/auth` and mounts the complete APEX
RAG, graph, agent, upload, frontend, approval, and report service under `/apex`.

Run the integrated backend from this directory:

```powershell
& ".venv/Scripts/python.exe" -m uvicorn app.main:app --reload
```

Integrated URLs:

- `http://127.0.0.1:8000/` - RefineShield health
- `http://127.0.0.1:8000/docs` - combined API docs
- `http://127.0.0.1:8000/auth/login` - real JWT login
- `http://127.0.0.1:8000/apex/app/` - APEX frontend
- `POST /apex/analysis/run?asset_id=P101` - LangGraph analysis
- `POST /apex/documents/upload` - document trust metadata
- `POST /apex/approvals/{approval_id}/approve` - approval decision

The APEX sub-application remains independently testable through its existing
tests. The integration tests in `testing/test_refineshield_integration.py`
verify that RefineShield and APEX are available in one backend process.

The integrated frontend includes both **Sign in** and **Create account** tabs.
Registration calls RefineShield `/auth/register`; login calls `/auth/login` and
stores only the returned access token in session storage. APEX requests send
that token as a bearer credential.

The original `venv` in this folder points to an unavailable Python 3.14
installation. Recreate it with an installed Python version before team use:

```powershell
Remove-Item -Recurse -Force .\venv
py -3.13 -m venv venv
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\venv\Scripts\python.exe" -m pip install -r requirements-apex.txt
```

Set the database and JWT values from `.env.example` before starting the real
RefineShield app. The mounted APEX service uses local in-memory Qdrant and the
local asset-graph fallback by default; Docker Qdrant/Neo4j can be enabled later
through `QDRANT_URL` and `NEO4J_*` variables.

## LangGraph approval pause/resume

High-risk analysis now pauses inside the LangGraph safety node with
`langgraph.types.interrupt`. The checkpoint is persisted locally in
`data/apex_checkpoints.sqlite` and the approval ID is also stored in the
RefineShield PostgreSQL `audit_logs` table.

The flow is:

```text
POST /apex/analysis/run
	-> HUMAN_APPROVAL_REQUIRED + approval_id + thread_id + interrupt
POST /apex/approvals/{approval_id}/approve
	-> Command(resume="approve")
	-> graph resumes and generates the report
```

Reject uses `Command(resume="reject")` and resumes the same checkpoint with a
rejected final approval status. The safety node is intentionally re-executed on
resume, which is normal LangGraph interrupt behavior. For multi-instance
production deployment, replace the local SQLite saver with a shared
PostgreSQL checkpointer package; PostgreSQL audit persistence is already active.

## Real JWT/RBAC behavior

The mounted APEX service uses RefineShield authentication rather than the old
standalone demo login:

1. Register or log in through `/auth/register` and `/auth/login`.
2. Send `Authorization: Bearer <access_token>` to protected `/apex` routes.
3. `ENGINEER` and `ADMIN` can upload and approve; viewers cannot.
4. Uploaded files, versions, and approval events are stored through the
	existing `documents`, `document_versions`, and `audit_logs` tables.

## Qwen and OpenRouter

OpenRouter can be used as a development-only Qwen provider through its
OpenAI-compatible API, but it sends document content outside the air-gapped
environment. That conflicts with the SIH sovereign-data claim, so the final
demo should use local Qwen2.5-VL or a local inference server.

If OpenRouter is used temporarily, use only synthetic documents and keep the
key outside Git:

```text
OPENROUTER_API_KEY=<local-secret>
OPENROUTER_MODEL=qwen/qwen2.5-vl-7b-instruct
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

TrustGate, validation, RBAC, human approval, and safety rules remain local and
deterministic even when the analyst model is remote.

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
- A standalone frontend is available at `/app/` for demo login, upload trust
	results, agent trace, evidence, approval, and report download.
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
- `POST /auth/demo-login`
- `POST /documents/upload`
- `GET /approvals/{approval_id}`
- `POST /approvals/{approval_id}/approve`
- `POST /approvals/{approval_id}/reject`
- `GET /reports/download`

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

## Standalone frontend demo

Start the API:

```powershell
& ".venv/Scripts/python.exe" -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000/app/` in a browser. The standalone UI uses demo
authentication and in-memory approval state. It validates the product flow
before the backend member integrates real JWT, RBAC, database persistence, and
TrustGate decisions. Uploaded files receive a SHA-256 fingerprint and trust
metadata; they are not automatically added to the seeded knowledge base until
the real TrustGate ingestion path is connected.

## Coordination needed

You can continue testing now. Ask the backend member to confirm whether their
service will mount this router or call `POST /query`. Ask the AI member to use
the returned `context` and `sources` fields. Ask the security member to provide
the final trust-status values and document IDs; the current adapter accepts
`trusted`, `pending`, and `quarantined` statuses.
