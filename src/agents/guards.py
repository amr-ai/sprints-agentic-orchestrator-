"""Pure graph branch guards, testable without Gemini or LangGraph."""

def _intent(state: dict) -> str:
    """Dispatch the learner to the selected Sprints worker or close a failed route."""
    return state.get("intent", "error")


def _rag_path(state: dict) -> str:
    """Allow one Advisor rewrite when retrieved curriculum evidence is insufficient."""
    if state.get("error") or not state.get("evidence"):
        return "answer"
    if state.get("context_sufficient"):
        return "answer"
    return "rewrite" if state.get("rag_attempts", 0) < 2 else "answer"


def _rewrite_path(state: dict) -> str:
    """Retry curriculum retrieval after a successful rewrite or surface the failure."""
    return "answer" if state.get("error") else "retrieve"


def _assessment_path(state: dict) -> str:
    """Send verified Python execution to feedback or surface the sandbox failure."""
    return "output" if state.get("error") else "feedback"


def _feedback_path(state: dict) -> str:
    """Send typed Sprints assessment feedback to the judge if generation succeeded."""
    return "output" if state.get("error") else "judge"


def _judge_path(state: dict) -> str:
    """Permit assessment feedback refinement until approval, failure, or attempt three."""
    if state.get("error") or state.get("judge_approved"):
        return "output"
    return "refine" if state.get("grading_attempts", 0) < 3 else "output"


def _career_path(state: dict) -> str:
    """Require human approval before releasing a tier-1 partner recommendation."""
    opening = state.get("matched_opening")
    return "approval" if opening and opening.get("tier_1") else "output"
