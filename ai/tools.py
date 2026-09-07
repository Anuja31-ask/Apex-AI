"""
Tools available to APEX-AI agents.

These tools connect the agent layer to the existing
RAG/API implementation.
"""

from typing import Any, Dict, List

import requests


# =========================================================
# Configuration
# =========================================================

RAG_API_URL = "http://localhost:8000/query"


# =========================================================
# Retrieval Tool
# =========================================================

def retrieve_evidence(
    query: str,
    limit: int = 5
) -> Dict[str, Any]:

    """
    Retrieve trusted evidence from the existing APEX-AI
    RAG API.

    The RAG service already performs trust-aware retrieval.
    """

    try:

        response = requests.post(
            RAG_API_URL,
            json={
                "query": query,
                "limit": limit
            },
            timeout=30
        )

        if response.status_code == 404:

            return {
                "context": [],
                "sources": [],
                "status": "INSUFFICIENT_EVIDENCE"
            }

        response.raise_for_status()

        data = response.json()

        context = data.get("context", [])

        sources = data.get("sources", [])

        # -------------------------------------------------
        # Extra safety check
        # -------------------------------------------------

        trusted_sources = []

        for source in sources:

            if source.get("trust_status") == "trusted":

                trusted_sources.append(source)

        if not trusted_sources:

            return {
                "context": [],
                "sources": [],
                "status": "INSUFFICIENT_EVIDENCE"
            }

        return {
            "context": context,
            "sources": trusted_sources,
            "status": "SUCCESS"
        }

    except requests.RequestException as exc:

        return {
            "context": [],
            "sources": [],
            "status": "ERROR",
            "error": str(exc)
        }


# =========================================================
# Evidence Formatting
# =========================================================

def format_evidence(
    context: List[str],
    sources: List[Dict[str, Any]]
) -> str:

    """
    Convert RAG results into a format suitable for the LLM.
    """

    if not context or not sources:

        return "No authoritative evidence found."

    formatted = []

    for index, text in enumerate(context):

        source = (
            sources[index]
            if index < len(sources)
            else {}
        )

        document = source.get(
            "document",
            "Unknown document"
        )

        page = source.get(
            "page",
            "Unknown page"
        )

        document_id = source.get(
            "document_id",
            "Unknown"
        )

        score = source.get(
            "score",
            0
        )

        formatted.append(
            f"""
EVIDENCE {index + 1}

Document: {document}
Page: {page}
Document ID: {document_id}
Retrieval Score: {score}

Content:
{text}
"""
        )

    return "\n".join(formatted)


# =========================================================
# Deterministic vibration validation
# =========================================================

def check_vibration(
    vibration: float,
    threshold: float
) -> Dict[str, Any]:

    """
    Deterministic numerical validation.

    The LLM should never be trusted to perform important
    threshold calculations when a deterministic function
    can do them.
    """

    exceeds_threshold = vibration > threshold

    return {
        "value": vibration,
        "threshold": threshold,
        "exceeds_threshold": exceeds_threshold,
        "status": (
            "ABOVE_THRESHOLD"
            if exceeds_threshold
            else "WITHIN_THRESHOLD"
        )
    }


# =========================================================
# Generic numeric comparison
# =========================================================

def compare_value(
    value: float,
    threshold: float,
    operator: str = ">"
) -> Dict[str, Any]:

    if operator == ">":

        result = value > threshold

    elif operator == ">=":

        result = value >= threshold

    elif operator == "<":

        result = value < threshold

    elif operator == "<=":

        result = value <= threshold

    elif operator == "==":

        result = value == threshold

    else:

        raise ValueError(
            f"Unsupported operator: {operator}"
        )

    return {
        "value": value,
        "threshold": threshold,
        "operator": operator,
        "result": result
    }