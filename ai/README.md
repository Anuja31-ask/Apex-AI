# Member 1 AI workflow

The LangGraph workflow is in `workflow.py`. It orchestrates:

```text
Planner -> Retrieval -> Analyst -> Validator -> Safety Governor -> Report
```

Member 4 services are called through the in-process `UnifiedContext` during
standalone tests. During team integration, the retrieval node can call the
backend's `POST /analysis/context` route and the report node can call
`POST /reports/diagnostic`.

## Required model handoff

The current analyst is intentionally deterministic and offline for the
synthetic P-101 demo. To enable Qwen2.5-VL-7B-Instruct, the team must provide:

- A local model directory or approved local model server URL
- GPU/CPU and VRAM availability
- The expected image/PDF preprocessing format
- The structured JSON output schema from the model

Qwen may suggest findings, but it must not decide trust, numerical comparisons,
permissions, quarantine, human approval, or physical control actions.