from __future__ import annotations

import re
from typing import Any

from rag.unified_context import UnifiedContext

from .state import AnalysisState


def _trace(state: AnalysisState, name: str) -> None:
    state.setdefault("agent_trace", []).append(name)


def planner_node(state: AnalysisState) -> AnalysisState:
    _trace(state, "Planner")
    state["plan"] = [
        "Extract inspection findings",
        "Retrieve SOP and maintenance evidence",
        "Compare vibration with the approved demonstration threshold",
        "Identify probable cause for investigation",
        "Validate evidence and recommendation",
        "Apply the safety governor",
        "Prepare the verified report",
    ]
    return state


def retrieval_node(state: AnalysisState, context_service: UnifiedContext) -> AnalysisState:
    _trace(state, "Retrieval")
    state["context"] = context_service.build(
        state["user_query"], state.get("asset_id", "P-101"), limit=5
    )
    return state


def _number(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def analyst_node(state: AnalysisState) -> AnalysisState:
    _trace(state, "Analyst")
    context = state.get("context", {})
    sources = context.get("sources", [])
    if not context.get("authoritative_evidence"):
        state["error"] = "No trusted evidence is available for this analysis."
        state["findings"] = {}
        state["model_used"] = "evidence-guard"
        return state

    evidence = " ".join(context.get("document_context", []))
    observed = _number(r"Observed vibration:\s*(\d+(?:\.\d+)?)", evidence)
    threshold = _number(r"(?:threshold|review threshold).*?is\s*(\d+(?:\.\d+)?)", evidence)
    temperature = _number(r"Temperature at bearing housing:\s*(\d+(?:\.\d+)?)", evidence)
    findings = {
        "issue": "Abnormal vibration",
        "observed_value": f"{observed:g} mm/s RMS" if observed is not None else "Not found",
        "threshold": f"{threshold:g} mm/s RMS" if threshold is not None else "Not found",
        "observed_vibration": observed,
        "threshold_value": threshold,
        "temperature": temperature,
        "probable_cause": "Bearing degradation for investigation",
        "recommendation": "Perform a detailed bearing inspection and review maintenance history",
        "sources": sources,
        "asset_relationships": context.get("asset_relationships", []),
    }
    state["findings"] = findings
    state["model_used"] = "local-evidence-analyst"
    return state


def validator_node(state: AnalysisState) -> AnalysisState:
    _trace(state, "Validator")
    findings = state.get("findings", {})
    observed = findings.get("observed_vibration")
    threshold = findings.get("threshold_value")
    has_sources = bool(findings.get("sources")) and all(
        source.get("trust_status") == "trusted" and source.get("page", 0) >= 1
        for source in findings.get("sources", [])
    )
    numeric_check = observed is not None and threshold is not None and observed > threshold
    validation = {
        "numerical_check": "PASS" if numeric_check else "FAIL",
        "source_check": "PASS" if has_sources else "FAIL",
        "evidence_check": "PASS" if state.get("context", {}).get("authoritative_evidence") else "FAIL",
        "rule_check": "PASS" if numeric_check else "REVIEW_REQUIRED",
        "validation_status": "PASS" if numeric_check and has_sources else "REVIEW_REQUIRED",
    }
    state["validation"] = validation
    state["risk"] = "HIGH" if numeric_check else "REVIEW"
    return state


def safety_node(state: AnalysisState) -> AnalysisState:
    _trace(state, "Safety Governor")
    if state.get("risk") == "HIGH":
        state["approval_status"] = "HUMAN_APPROVAL_REQUIRED"
    else:
        state["approval_status"] = "REVIEW_REQUIRED"
    return state


def report_node(state: AnalysisState) -> AnalysisState:
    _trace(state, "Report Preparation")
    findings = state.get("findings", {})
    state["report_payload"] = {
        "asset_id": state.get("asset_id", "P-101"),
        **findings,
        "risk": state.get("risk", "REVIEW"),
        "approval_status": state.get("approval_status", "REVIEW_REQUIRED"),
        "validations": [
            f"Numerical validation: {state.get('validation', {}).get('numerical_check', 'FAIL')}",
            f"Source verification: {state.get('validation', {}).get('source_check', 'FAIL')}",
            f"Safety rule validation: {state.get('validation', {}).get('rule_check', 'FAIL')}",
        ],
        "audit_id": "AUD-P101-DEMO",
    }
    _trace(state, "Report Ready")
    return state