"""
LangGraph workflow for APEX-AI.

Workflow:

START
  ↓
PLANNER
  ↓
RETRIEVER
  ↓
ANALYST
  ↓
VALIDATOR
  ↓
FINAL
"""

from typing import Any, Dict

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from .state import AgentState
from .agents import (
    planner_agent,
    analyst_agent,
    validator_agent,
)
from .tools import retrieve_evidence


# =========================================================
# Planner Node
# =========================================================

def planner_node(
    state: AgentState
) -> Dict[str, Any]:

    query = state["query"]

    result = planner_agent(query)

    completed = state.get(
        "completed_agents",
        []
    ).copy()

    completed.append("Planner")

    return {
        "plan": result,
        "current_agent": "Planner",
        "completed_agents": completed
    }


# =========================================================
# Retriever Node
# =========================================================

def retriever_node(
    state: AgentState
) -> Dict[str, Any]:

    query = state["query"]

    result = retrieve_evidence(
        query,
        limit=5
    )

    print("\n========== RETRIEVER DEBUG ==========")
    print("Status:", result.get("status"))
    print("Context count:", len(result.get("context", [])))
    print("Sources count:", len(result.get("sources", [])))
    print("Sources:", result.get("sources", []))
    print("=====================================\n")

    completed = state.get(
        "completed_agents",
        []
    ).copy()

    completed.append("Retriever")

    return {
        "context": result.get(
            "context",
            []
        ),

        "sources": result.get(
            "sources",
            []
        ),

        "current_agent": "Retriever",

        "completed_agents": completed
    }
# =========================================================
# Analyst Node
# =========================================================

def analyst_node(
    state: AgentState
) -> Dict[str, Any]:

    context = state.get(
        "context",
        []
    )

    sources = state.get(
        "sources",
        []
    )

    query = state["query"]

    # -----------------------------------------------------
    # No evidence
    # -----------------------------------------------------

    if not context or not sources:

        completed = state.get(
            "completed_agents",
            []
        )

        completed.append("Analyst")

        return {
            "analysis": {
                "summary": (
                    "No authoritative evidence "
                    "was found."
                ),
                "observed_facts": [],
                "probable_causes": [],
                "recommendations": [],
                "confidence": 0.0
            },

            "current_agent": "Analyst",

            "completed_agents": completed
        }

    result = analyst_agent(
        query,
        context,
        sources
    )

    completed = state.get(
        "completed_agents",
        []
    )

    completed.append("Analyst")

    return {
        "analysis": result,
        "current_agent": "Analyst",
        "completed_agents": completed
    }


# =========================================================
# Validator Node
# =========================================================

def validator_node(
    state: AgentState
) -> Dict[str, Any]:

    analysis = state.get(
        "analysis",
        {}
    )

    sources = state.get(
        "sources",
        []
    )

    query = state["query"]

    # -----------------------------------------------------
    # No evidence
    # -----------------------------------------------------

    if not sources:

        result = {
            "validation_status": "INSUFFICIENT_EVIDENCE",
            "verified_claims": [],
            "issues": [
                "No authoritative evidence was retrieved."
            ],
            "risk_level": "UNKNOWN",
            "human_approval_required": True
        }

    else:

        result = validator_agent(
            query,
            analysis,
            sources
        )

    # -----------------------------------------------------
    # Deterministic safety override
    # -----------------------------------------------------

    recommendations = analysis.get(
        "recommendations",
        []
    )

    recommendation_text = " ".join(
        recommendations
    ).lower()

    high_risk_keywords = [
        "shutdown",
        "shut down",
        "isolate",
        "isolation",
        "pressure release",
        "electrical intervention",
        "emergency stop",
        "stop operation",
        "stop the pump",
    ]

    if any(
        keyword in recommendation_text
        for keyword in high_risk_keywords
    ):

        result["human_approval_required"] = True

        if result.get("risk_level") == "LOW":
            result["risk_level"] = "HIGH"

        result["issues"] = result.get(
            "issues",
            []
        )

        result["issues"].append(
            "High-risk industrial action detected. "
            "Human approval is required."
        )

    # -----------------------------------------------------
    # Mark Validator as completed
    # -----------------------------------------------------

    completed = state.get(
        "completed_agents",
        []
    ).copy()

    completed.append("Validator")

    return {
        "validation": result,
        "current_agent": "Validator",
        "completed_agents": completed
    }

# =========================================================
# Final Node
# =========================================================

def final_node(
    state: AgentState
) -> Dict[str, Any]:

    sources = state.get(
        "sources",
        []
    )

    analysis = state.get(
        "analysis",
        {}
    )

    validation = state.get(
        "validation",
        {}
    )

    # -----------------------------------------------------
    # No evidence
    # -----------------------------------------------------

    if not sources:

        final_result = {

            "status":
                "INSUFFICIENT_EVIDENCE",

            "message":
                "No authoritative evidence found.",

            "summary":
                "The requested analysis cannot be "
                "reliably completed because no "
                "authoritative evidence was retrieved.",

            "observed_facts": [],

            "probable_causes": [],

            "recommendations": [],

            "evidence": [],

            "validation_status":
                "INSUFFICIENT_EVIDENCE",

            "risk_level":
                "UNKNOWN",

            "confidence":
                0.0,

            "human_approval_required":
                True
        }

    else:

        final_result = {

            "status": "SUCCESS",

            "summary":
                analysis.get(
                    "summary",
                    ""
                ),

            "observed_facts":
                analysis.get(
                    "observed_facts",
                    []
                ),

            "probable_causes":
                analysis.get(
                    "probable_causes",
                    []
                ),

            "recommendations":
                analysis.get(
                    "recommendations",
                    []
                ),

            "evidence":
                sources,

            "validation_status":
                validation.get(
                    "validation_status",
                    "UNKNOWN"
                ),

            "risk_level":
                validation.get(
                    "risk_level",
                    "UNKNOWN"
                ),

            "confidence":
                analysis.get(
                    "confidence",
                    0
                ),

            "human_approval_required":
                validation.get(
                    "human_approval_required",
                    True
                )
        }

    return {
        "final_result": final_result,
        "current_agent": "Final"
    }


# =========================================================
# Build graph
# =========================================================

def build_graph():

    workflow = StateGraph(
        AgentState
    )

    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------

    workflow.add_node(
        "planner",
        planner_node
    )

    workflow.add_node(
        "retriever",
        retriever_node
    )

    workflow.add_node(
        "analyst",
        analyst_node
    )

    workflow.add_node(
        "validator",
        validator_node
    )

    workflow.add_node(
        "final",
        final_node
    )

    # -----------------------------------------------------
    # Edges
    # -----------------------------------------------------

    workflow.add_edge(
        START,
        "planner"
    )

    workflow.add_edge(
        "planner",
        "retriever"
    )

    workflow.add_edge(
        "retriever",
        "analyst"
    )

    workflow.add_edge(
        "analyst",
        "validator"
    )

    workflow.add_edge(
        "validator",
        "final"
    )

    workflow.add_edge(
        "final",
        END
    )

    return workflow.compile()


# ---------------------------------------------------------
# Compiled graph
# ---------------------------------------------------------

agent_graph = build_graph()