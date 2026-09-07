from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from rag.unified_context import UnifiedContext

from .nodes import analyst_node, planner_node, report_node, retrieval_node, safety_node, validator_node
from .state import AnalysisState


def build_workflow(context_service: UnifiedContext):
    """Build the SIH workflow with explicit, inspectable LangGraph nodes."""

    graph = StateGraph(AnalysisState)
    graph.add_node("planner", planner_node)
    graph.add_node("retrieval", lambda state: retrieval_node(state, context_service))
    graph.add_node("analyst", analyst_node)
    graph.add_node("validator", validator_node)
    graph.add_node("safety_governor", safety_node)
    graph.add_node("report", report_node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "retrieval")
    graph.add_edge("retrieval", "analyst")
    graph.add_edge("analyst", "validator")
    graph.add_edge("validator", "safety_governor")
    graph.add_edge("safety_governor", "report")
    graph.add_edge("report", END)
    return graph.compile()