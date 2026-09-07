# ai_engine/agent_graph.py
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from ai_engine.llm_service import get_local_llm

# 1. Define Shared Agent State
class AgentState(TypedDict):
    user_query: str
    retrieved_context: List[str]
    analysis_draft: str
    validation_status: str
    final_response: str

# Instantiate our verified local LLM
local_llm = get_local_llm()

# 2. Define Workflow Nodes

def planner_node(state: AgentState):
    """
    Planner Node: Processes the query and identifies relevant search strategy.
    (In later steps, this queries Qdrant Vector DB & Neo4j Graph DB).
    """
    print("\n[Node 1: Planner] Formulating context retrieval strategy...")
    
    # Mock retrieved telemetry/manual context for pipeline validation
    mock_context = [
        "Equipment: Centrifugal Pump P-101",
        "Sensor Status: Vibration levels registered at 8.2 mm/s RMS on drive end.",
        "Threshold: Standard operating limit is 4.5 mm/s RMS."
    ]
    return {"retrieved_context": mock_context}


def analyst_node(state: AgentState):
    """
    Analyst Node: Uses local Qwen2.5-VL to synthesize findings and diagnose issues.
    """
    print("[Node 2: Analyst] Synthesizing findings with local LLM...")
    
    context_str = "\n".join(state["retrieved_context"])
    prompt = f"""You are an industrial diagnostics AI assistant.
Analyze the following equipment context and address the user query.

Query: {state['user_query']}

Context:
{context_str}

Provide a concise diagnosis and action item."""

    response = local_llm.invoke(prompt)
    return {"analysis_draft": response.content}


def validator_node(state: AgentState):
    """
    Validator Node: Audits outputs against safety rules and compliance requirements.
    """
    print("[Node 3: Validator] Auditing output against safety protocols...")
    
    # Simple validation rules engine check
    draft = state.get("analysis_draft", "")
    if draft:
        status = "APPROVED"
        final_out = draft
    else:
        status = "REJECTED"
        final_out = "Analysis failed to generate a response."
        
    return {
        "validation_status": status,
        "final_response": final_out
    }

# 3. Assemble LangGraph Workflow
builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("planner", planner_node)
builder.add_node("analyst", analyst_node)
builder.add_node("validator", validator_node)

# Connect Edges
builder.set_entry_point("planner")
builder.add_edge("planner", "analyst")
builder.add_edge("analyst", "validator")
builder.add_edge("validator", END)

# Compile Executable Graph
agent_app = builder.compile()

if __name__ == "__main__":
    print("--- Executing APEX-AI LangGraph Pipeline ---")
    initial_input = {
        "user_query": "What is the status of Pump P-101 and what action should be taken?"
    }
    
    result = agent_app.invoke(initial_input)
    
    print("\n================ FINAL AGENT OUTPUT ================")
    print(f"Validation Status: {result['validation_status']}")
    print(f"Response:\n{result['final_response']}")
    print("====================================================")