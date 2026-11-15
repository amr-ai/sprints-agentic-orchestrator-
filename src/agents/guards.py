"""Pure graph branch guards, testable without Gemini or LangGraph."""

def _intent(state: dict) -> str:
    return state.get("intent", "error")


def _rag_path(state: dict) -> str:
    if state.get("error") or not state.get("evidence"):
        return "answer"
    if state.get("context_sufficient"):
        return "answer"
    return "rewrite" if state.get("rag_attempts", 0) < 2 else "answer"


def _rewrite_path(state: dict) -> str:
    return "answer" if state.get("error") else "retrieve"


def _assessment_path(state: dict) -> str:
    return "output" if state.get("error") else "feedback"


def _feedback_path(state: dict) -> str:
    return "output" if state.get("error") else "judge"


def _judge_path(state: dict) -> str:
    if state.get("error") or state.get("judge_approved"):
        return "output"
    return "refine" if state.get("grading_attempts", 0) < 3 else "output"


def _career_path(state: dict) -> str:
    opening = state.get("matched_opening")
    return "approval" if opening and opening.get("tier_1") else "output"
