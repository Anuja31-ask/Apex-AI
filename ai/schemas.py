"""
Structured data models used by APEX-AI agents.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# =========================================================
# Planner
# =========================================================

class PlannerOutput(BaseModel):

    objective: str = Field(
        description="The objective of the analysis."
    )

    steps: List[str] = Field(
        description="Ordered reasoning steps."
    )

    requires_calculation: bool = False

    requires_safety_check: bool = False


# =========================================================
# Evidence
# =========================================================

class Evidence(BaseModel):

    document: str

    page: Optional[int] = None

    document_id: Optional[str] = None

    trust_status: str = "unknown"

    score: Optional[float] = None

    text: str


# =========================================================
# Analyst
# =========================================================

class AnalystOutput(BaseModel):

    summary: str

    observed_facts: List[str]

    probable_causes: List[str]

    recommendations: List[str]

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )


# =========================================================
# Validator
# =========================================================

class ValidatorOutput(BaseModel):

    validation_status: str

    verified_claims: List[str]

    issues: List[str]

    risk_level: str

    human_approval_required: bool


# =========================================================
# Final Analysis
# =========================================================

class FinalAnalysis(BaseModel):

    status: str

    summary: str

    observed_facts: List[str]

    probable_causes: List[str]

    recommendations: List[str]

    evidence: List[Evidence]

    validation_status: str

    risk_level: str

    confidence: float

    human_approval_required: bool

    message: Optional[str] = None