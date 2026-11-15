"""No learner-supplied code must execute on the host in offline tests."""
import pytest
from src.schemas import GradeFeedback, unable_to_verify
from src.tools import code_repl


def test_strict_grade_feedback():
    good = GradeFeedback(score=100, feedback_points=["All tests passed"], pass_status=True)
    assert good.score == 100
    with pytest.raises(Exception):
        GradeFeedback(score=110, feedback_points=["No"], pass_status=True)


def test_sandbox_fails_closed_when_docker_unavailable(monkeypatch):
    monkeypatch.setattr(code_repl.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="refusing unsafe host code execution"):
        code_repl.execute_submission("print('unsafe')", "sum_two")


def test_generic_tool_failure_is_structured():
    error = unable_to_verify("sqlite", "connection failed")
    assert error["status"] == "Unable to verify"
    assert error["tool"] == "sqlite"


def test_rubric_contains_explicit_cases():
    rubric = code_repl.load_rubric("sum_two")
    assert rubric["pass_threshold"] == 70
    assert len(rubric["tests"]) == 3
