"""Docker-based Sprints Python assessment, model feedback, and judge loop."""
from langchain_core.prompts import ChatPromptTemplate
from src.config import chat_model
from src.schemas import GradeFeedback, JudgeDecision, unable_to_verify
from src.tools.code_repl import execute_submission, load_rubric

FEEDBACK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Sprints Python Assessor. Produce the required
    Pydantic JSON fields: score, feedback_points, pass_status. The score and
    pass_status MUST reflect the deterministic execution results, never your
    imagination. Give concise actionable feedback based ONLY on test output."""),
    ("human", "Assignment rubric: {rubric}\nVerified test results: {execution}\n"
              "Required score: {score}\nRequired pass_status: {passed}\n"
              "Additional judge feedback: {improvement}"),
])
JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an independent evaluator. Approve the Sprints
    assessor feedback only if score and pass_status exactly match the
    deterministic tests and feedback has no fabricated runtime behavior.
    Provide reason and targeted improvement if rejecting."""),
    ("human", "Rubric: {rubric}\nExecution: {execution}\nFeedback: {feedback}"),
])


def run_submission_node(state: dict) -> dict:
    """Run PythonREPL in Docker, never in the main LangGraph process."""
    try:
        result = execute_submission(state.get("submission_code", ""),
                                    state.get("assignment_id", "sum_two"))
        return {"execution": result}
    except Exception as exc:
        return {"error": unable_to_verify("docker_python_repl", str(exc)),
                "answer": "Unable to verify: sandbox grading unavailable; no grade awarded."}


def write_feedback_node(state: dict) -> dict:
    """Create typed grading feedback, enforcing deterministic score bounds."""
    try:
        execution = state["execution"]
        expected_score = execution["score"]
        expected_pass = expected_score >= execution["pass_threshold"]
        rubric = load_rubric(state.get("assignment_id", "sum_two"))
        result = (FEEDBACK_PROMPT | chat_model().with_structured_output(
            GradeFeedback, method="json_schema"
        )).invoke({"rubric": rubric, "execution": execution,
                  "score": expected_score, "passed": expected_pass,
                  "improvement": state.get("judge_improvement", "")})
        # The model cannot overrule executed test outcomes.
        feedback = result.model_dump()
        feedback["score"] = expected_score
        feedback["pass_status"] = expected_pass
        return {"feedback": feedback, "grading_attempts": state.get("grading_attempts", 0) + 1}
    except Exception as exc:
        return {"error": unable_to_verify("gemini_assessor", str(exc)),
                "answer": "Unable to verify: grading feedback unavailable."}


def judge_node(state: dict) -> dict:
    """Verify rubric and grade consistency through a separate model call."""
    try:
        result = (JUDGE_PROMPT | chat_model().with_structured_output(
            JudgeDecision, method="json_schema"
        )).invoke({"rubric": load_rubric(state.get("assignment_id", "sum_two")),
                  "execution": state["execution"], "feedback": state["feedback"]})
        expected = state["execution"]["score"]
        consistent = (state["feedback"].get("score") == expected and
                      state["feedback"].get("pass_status") ==
                      (expected >= state["execution"]["pass_threshold"]))
        return {"judge_approved": bool(result.approved and consistent),
                "judge_improvement": result.improvement or result.reason}
    except Exception as exc:
        return {"judge_approved": False,
                "error": unable_to_verify("gemini_judge", str(exc))}


def grade_output_node(state: dict) -> dict:
    """Return the verified Sprints grade, or explain why grading stopped."""
    if state.get("error") and state.get("answer"):
        return {"answer": state["answer"]}
    if state.get("judge_approved") and not state.get("error"):
        feedback = state["feedback"]
        return {"answer": (
            f"Grading verified in the DEMO sandbox: {feedback['score']}/100; "
            f"pass_status={feedback['pass_status']}. "
            f"Tests: {state['execution']['passed_tests']}/{state['execution']['total_tests']}. "
            f"Feedback: {'; '.join(feedback['feedback_points'])}"
        )}
    return {"answer": "Unable to verify: assessment did not pass independent review "
                      "within 3 feedback attempts; no final grade awarded."}
