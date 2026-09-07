# Member 4 Integration Contract

## Unified analysis context

`POST /analysis/context?asset_id=P101`

Request:

```json
{
  "query": "Analyze P-101 vibration and identify related assets.",
  "limit": 5
}
```

Response fields:

- `document_context`: trusted Qdrant text chunks
- `sources`: document, page, document ID, trust status, and score
- `asset_id`: normalized format such as `P-101`
- `asset_relationships`: Neo4j or local graph relationships
- `authoritative_evidence`: false when no trusted sources were retrieved

Qdrant answers document-fact questions. Neo4j answers asset-relationship
questions. The AI member should use both and cite only the returned `sources`.

## Report generation

`POST /reports/diagnostic` accepts the AI/validator result as JSON and returns a
PDF. Important fields include `asset_id`, `issue`, `observed_value`, `threshold`,
`probable_cause`, `risk`, `recommendation`, `approval_status`, `sources`,
`asset_relationships`, `validations`, and `audit_id`.

## Audit events

The standalone service writes JSON Lines to `reports/audit.log.jsonl` for:

- `RAG_QUERY`
- `DOCUMENT_RETRIEVED`
- `GRAPH_QUERY`
- `AGENT_CONTEXT_CREATED`
- `REPORT_GENERATED`

The backend member can later replace this local writer with the team audit
database while preserving the event names and fields.