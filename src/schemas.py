"""Strict contracts used for routing, scoring, retrieval and safe fallbacks."""
from typing import Literal
from pydantic import BaseModel, Field


class RouteDecision(BaseModel):
    """Constrain learner requests to the four supported Sprints worker routes."""

    intent: Literal["advisor", "assessor", "career", "learner_record"]


class ContextAssessment(BaseModel):
    """Record whether retrieved curriculum excerpts support the Advisor answer and why."""

    sufficient: bool
    reason: str


class Rewrite(BaseModel):
    """Carry the Advisor's reformulated query into its second curriculum search."""

    reformulated_query: str


class GradeFeedback(BaseModel):
    """Validate Sprints Python feedback with a 0–100 score and rubric pass flag."""

    score: int = Field(ge=0, le=100)
    feedback_points: list[str] = Field(min_length=1)
    pass_status: bool


class JudgeDecision(BaseModel):
    """Record the Assessor judge's rubric review and guidance for another attempt."""

    approved: bool
    reason: str
    improvement: str = ""


class VerifiedError(BaseModel):
    """Identify which Sprints tool or worker could not verify a learner outcome."""

    status: Literal["Unable to verify"] = "Unable to verify"
    reason: str
    tool: str


def unable_to_verify(tool: str, reason: str) -> dict:
    """Fail closed instead of inventing database, curriculum or grade claims."""
    return VerifiedError(tool=tool, reason=reason).model_dump()
