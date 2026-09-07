from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUDIT_LOG = Path(__file__).parents[1] / "reports" / "audit.log.jsonl"


def record_event(event_type: str, **details: Any) -> dict[str, Any]:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        **details,
    }
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as log:
        log.write(json.dumps(event) + "\n")
    return event