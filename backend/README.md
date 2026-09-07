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
- `GET /graph/assets/P101`
- `GET /graph/assets/P101/relationships/DRIVEN_BY`

The current default uses in-memory Qdrant and local embeddings. Set `QDRANT_URL`
to use a running Qdrant service later. These internal endpoints contain synthetic,
read-only demo data and are not MRPL integrations.

## Neo4j graph mode

The graph API uses a local fallback until `NEO4J_URI` and `NEO4J_PASSWORD` are
set. Start Neo4j with Docker:

```powershell
docker run --name neo4j-apex -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password123 neo4j:5
```

Set the variables in the current PowerShell session:

```powershell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USERNAME="neo4j"
$env:NEO4J_PASSWORD="password123"
$env:NEO4J_DATABASE="neo4j"
```

Seed the graph once:

```powershell
python -m graph.seed
```

The same graph API then queries Neo4j instead of the local fallback. The graph
contains only synthetic P-101 relationships and is not a live MRPL system.
