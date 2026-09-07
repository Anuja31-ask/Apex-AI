"""
APEX-AI agents.

Agents:
    1. Planner
    2. Analyst
    3. Validator

The retrieval component is treated as a tool rather than
an independent LLM agent.
"""

from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from .llm import get_llm
from .prompts import (
    PLANNER_SYSTEM_PROMPT,
    ANALYST_SYSTEM_PROMPT,
    VALIDATOR_SYSTEM_PROMPT,
)
from .schemas import (
    PlannerOutput,
    AnalystOutput,
    ValidatorOutput,
)
from .tools import format_evidence


# =========================================================
# Planner Agent
# =========================================================

def planner_agent(
    query: str
) -> Dict[str, Any]:

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        PlannerOutput
    )

    messages = [

        SystemMessage(
            content=PLANNER_SYSTEM_PROMPT
        ),

        HumanMessage(
            content=query
        )

    ]

    result = structured_llm.invoke(messages)

    return result.model_dump()


# =========================================================
# Analyst Agent
# =========================================================

def analyst_agent(
    query: str,
    context,
    sources
) -> Dict[str, Any]:

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        AnalystOutput
    )

    evidence = format_evidence(
        context,
        sources
    )

    prompt = f"""
USER REQUEST:

{query}


AUTHORITATIVE EVIDENCE:

{evidence}


Analyze the request using ONLY the evidence above.
"""

    messages = [

        SystemMessage(
            content=ANALYST_SYSTEM_PROMPT
        ),

        HumanMessage(
            content=prompt
        )

    ]

    result = structured_llm.invoke(messages)

    return result.model_dump()


# =========================================================
# Validator Agent
# =========================================================

def validator_agent(
    query: str,
    analysis: Dict[str, Any],
    sources
) -> Dict[str, Any]:

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        ValidatorOutput
    )

    prompt = f"""
USER REQUEST:

{query}


ANALYST RESULT:

{analysis}


AVAILABLE SOURCES:

{sources}


Validate the analysis against the available sources.

Important:

If evidence does not support an important claim,
mark it as unverified.

If the recommendation involves potentially dangerous
industrial action such as shutdown, isolation, pressure
release, electrical intervention, or physical maintenance,
human approval is required.
"""

    messages = [

        SystemMessage(
            content=VALIDATOR_SYSTEM_PROMPT
        ),

        HumanMessage(
            content=prompt
        )

    ]

    result = structured_llm.invoke(messages)

    return result.model_dump()