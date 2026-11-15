"""Strict contracts used for routing, scoring, retrieval and safe fallbacks."""
from typing import Literal
from pydantic import BaseModel, Field


class RouteDecision(BaseModel):
    intent: Literal["advisor", "assessor", "career", "learner_record"]


class ContextAssessment(BaseModel):
    sufficient: bool
    reason: str


class Rewrite(BaseModel):
    reformulated_query: str


class GradeFeedback(BaseModel):
    score: int = Field(ge=0, le=100)
    feedback_points: list[str] = Field(min_length=1)
    pass_status: bool


class JudgeDecision(BaseModel):
    approved: bool
    reason: str
    improvement: str = ""


class VerifiedError(BaseModel):
    status: Literal["Unable to verify"] = "Unable to verify"
    reason: str
    tool: str


def unable_to_verify(tool: str, reason: str) -> dict:
    """Fail closed instead of inventing database, curriculum or grade claims."""
    return VerifiedError(tool=tool, reason=reason).model_dump()
