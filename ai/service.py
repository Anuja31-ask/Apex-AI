"""
Public service interface for APEX-AI.

Backend should call:

    run_analysis(query)

instead of interacting directly with LangGraph.
"""

from typing import Any, Dict

from .graph import agent_graph


def run_analysis(
    query: str
) -> Dict[str, Any]:

    """
    Run the complete APEX-AI workflow.

    Planner
        ↓
    Retriever
        ↓
    Analyst
        ↓
    Validator
        ↓
    Final
    """

    if not query or not query.strip():

        return {
            "status": "ERROR",
            "message": "Query cannot be empty."
        }

    initial_state = {

        "query": query,

        "plan": {},

        "context": [],

        "sources": [],

        "analysis": {},

        "validation": {},

        "final_result": {},

        "current_agent": "",

        "completed_agents": [],

        "error": None
    }

    try:

        result = agent_graph.invoke(
            initial_state
        )

        final_result = result.get(
            "final_result",
            {}
        )

        return {

            "status":
                final_result.get(
                    "status",
                    "ERROR"
                ),

            "query":
                query,

            "workflow":
                result.get(
                    "completed_agents",
                    []
                ),

            "plan":
                result.get(
                    "plan",
                    {}
                ),

            "analysis":
                result.get(
                    "analysis",
                    {}
                ),

            "validation":
                result.get(
                    "validation",
                    {}
                ),

            "evidence":
                result.get(
                    "sources",
                    []
                ),

            "result":
                final_result
        }

    except Exception as exc:

        return {

            "status": "ERROR",

            "query": query,

            "workflow":
                initial_state[
                    "completed_agents"
                ],

            "error":
                str(exc)
        }