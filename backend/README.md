# Member 4 service adapter

Run from the repository root:

```powershell
python -m uvicorn backend.main:app --reload
```

The service is intentionally standalone while the team backend is being built.

- `GET /health`
- `POST /query` with `{ "query": "...", "limit": 5 }`
- `GET /internal/assets/P101`
- `GET /internal/maintenance/P101`
- `GET /internal/sensors/P101`

The current default uses in-memory Qdrant and local embeddings. Set `QDRANT_URL`
to use a running Qdrant service later. These internal endpoints contain synthetic,
read-only demo data and are not MRPL integrations.
