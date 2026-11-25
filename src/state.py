"""Global typed state of the unified Sprints LangGraph StateGraph."""
from typing import Annotated, Any, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class SprintsState(TypedDict, total=False):
    """Checkpoint Sprints learner messages and share evidence across workers for a turn.

    Retrieval timing is absent or None until the Advisor completes a search.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    learner_id: str
    query: str
    submission_code: str
    assignment_id: str
    intent: str
    answer: str
    evidence: list[dict]
    retrieval_ms: float | None
    context_sufficient: bool
    search_query: str
    judge_approved: bool
    judge_improvement: str
    tool_trace: list[str]
    rag_attempts: int
    grading_attempts: int
    execution: dict[str, Any]
    feedback: dict[str, Any]
    matched_opening: dict[str, Any] | None
    approval: dict[str, Any] | None
    error: dict[str, Any] | None
