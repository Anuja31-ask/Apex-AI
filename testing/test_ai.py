"""
Tests for APEX-AI agent workflow.
"""

from unittest.mock import patch

from ai.service import run_analysis
from ai.tools import (
    check_vibration,
    compare_value,
)


# =========================================================
# Deterministic calculation tests
# =========================================================

def test_vibration_above_threshold():

    result = check_vibration(
        vibration=8.5,
        threshold=7.1
    )

    assert result["exceeds_threshold"] is True

    assert (
        result["status"]
        == "ABOVE_THRESHOLD"
    )


def test_vibration_within_threshold():

    result = check_vibration(
        vibration=4.0,
        threshold=7.1
    )

    assert result["exceeds_threshold"] is False

    assert (
        result["status"]
        == "WITHIN_THRESHOLD"
    )


def test_compare_value():

    result = compare_value(
        value=10,
        threshold=5,
        operator=">"
    )

    assert result["result"] is True


# =========================================================
# Retrieval failure
# =========================================================

@patch(
    "ai.tools.retrieve_evidence"
)
def test_no_authoritative_evidence(
    mock_retrieval
):

    mock_retrieval.return_value = {

        "context": [],

        "sources": [],

        "status":
            "INSUFFICIENT_EVIDENCE"
    }

    result = run_analysis(
        "Analyze Pump P-101."
    )

    assert (
        result["status"]
        == "INSUFFICIENT_EVIDENCE"
    )


# =========================================================
# Trusted evidence
# =========================================================

@patch(
    "ai.tools.retrieve_evidence"
)
@patch(
    "ai.graph.planner_agent"
)
@patch(
    "ai.graph.analyst_agent"
)
@patch(
    "ai.graph.validator_agent"
)
def test_workflow(
    mock_validator,
    mock_analyst,
    mock_planner,
    mock_retrieval
):

    mock_retrieval.return_value = {

        "context": [
            "Pump P-101 vibration measured at 8.5 mm/s."
        ],

        "sources": [

            {
                "document":
                    "01_P101_Inspection_Report.pdf",

                "page": 4,

                "document_id":
                    "P101-INS-001",

                "trust_status":
                    "trusted",

                "score":
                    0.91
            }

        ],

        "status":
            "SUCCESS"
    }

    mock_planner.return_value = {

        "objective":
            "Analyze Pump P-101 vibration.",

        "steps": [
            "Review vibration evidence.",
            "Check maintenance history.",
            "Assess probable cause."
        ],

        "requires_calculation":
            True,

        "requires_safety_check":
            True
    }

    mock_analyst.return_value = {

        "summary":
            "Pump P-101 shows abnormal vibration.",

        "observed_facts": [
            "Vibration is 8.5 mm/s."
        ],

        "probable_causes": [
            "Possible mechanical imbalance."
        ],

        "recommendations": [
            "Inspect the pump before continued operation."
        ],

        "confidence":
            0.91
    }

    mock_validator.return_value = {

        "validation_status":
            "VALIDATED",

        "verified_claims": [
            "Vibration measurement is supported."
        ],

        "issues": [],

        "risk_level":
            "MEDIUM",

        "human_approval_required":
            False
    }

    result = run_analysis(
        "Analyze Pump P-101 vibration."
    )

    assert result["status"] == "SUCCESS"

    assert (
        "Planner"
        in result["workflow"]
    )

    assert (
        "Retriever"
        in result["workflow"]
    )

    assert (
        "Analyst"
        in result["workflow"]
    )

    assert (
        "Validator"
        in result["workflow"]
    )