"""Gemini intent router for the unified Sprints LangGraph orchestrator."""
from langchain_core.prompts import ChatPromptTemplate
from src.config import gemini_model
from src.schemas import RouteDecision, unable_to_verify

ROUTING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Route Sprints student requests to exactly one worker:
    advisor: curriculum, course, lesson or concept questions;
    assessor: submitted Python code, evaluation, marking, grade;
    career: partner roles, placement or job matching;
    learner_record: student's modules, progress, salary, employers, status.
    Return the route schema. Never create new learner facts."""),
    ("human", "Learner query: {query}"),
])


def route_node(state: dict) -> dict:
    """Reset transient state each turn and route by Pydantic-constrained Gemini intent."""
    query = state.get("query", "").strip()
    code = state.get("submission_code", "")
    if code.strip():
        intent = "assessor"
    else:
        try:
            intent = (ROUTING_PROMPT | gemini_model().with_structured_output(
                RouteDecision, method="json_schema"
            )).invoke({"query": query}).intent
        except Exception as exc:
            return {"intent": "error", "error": unable_to_verify("intent_router", str(exc)),
                    "answer": "Unable to verify: Gemini router unavailable."}
    return {"intent": intent, "answer": "", "error": None, "evidence": [],
            "rag_attempts": 0, "grading_attempts": 0,
            "feedback": {}, "execution": {}, "matched_opening": None,
            "approval": None, "search_query": "", "context_sufficient": False,
            "judge_approved": False, "judge_improvement": "", "tool_trace": []}
