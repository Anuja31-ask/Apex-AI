from __future__ import annotations

from typing import Any, TypedDict


class AnalysisState(TypedDict, total=False):
    user_query: str
    asset_id: str
    plan: list[str]
    context: dict[str, Any]
    findings: dict[str, Any]
    validation: dict[str, Any]
    risk: str
    approval_status: str
    agent_trace: list[str]
    report_payload: dict[str, Any]
    report_path: str
    model_used: str
    error: str
    human_decision: str
    human_decision: str