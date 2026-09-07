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
```

API contract:

- `GET /health`
- `POST /query` with `{ "query": "...", "limit": 5 }`
- `GET /internal/assets/P101`
- `GET /internal/maintenance/P101`
- `GET /internal/sensors/P101`

The internal endpoints contain synthetic, read-only data. They are placeholders
for authorized enterprise adapters and are not MRPL SAP/DCS integrations.

## Qdrant modes

Without `QDRANT_URL`, the API uses in-memory Qdrant and needs no credentials.
For a running local Qdrant service, copy `.env.example` to `.env` and set:

```text
QDRANT_URL=http://localhost:6333
```

The later Neo4j phase will use the reserved `NEO4J_*` variables in `.env`.

## Coordination needed

You can continue testing now. Ask the backend member to confirm whether their
service will mount this router or call `POST /query`. Ask the AI member to use
the returned `context` and `sources` fields. Ask the security member to provide
the final trust-status values and document IDs; the current adapter accepts
`trusted`, `pending`, and `quarantined` statuses.
