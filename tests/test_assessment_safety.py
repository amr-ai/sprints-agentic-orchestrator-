"""No learner-supplied code must execute on the host in offline tests."""
import subprocess
from unittest.mock import MagicMock, Mock

import pytest
from src.schemas import GradeFeedback, unable_to_verify
from src.tools import code_repl


def test_strict_grade_feedback():
    """Require the Assessor's typed grade to stay within the Sprints scoring range."""
    good = GradeFeedback(score=100, feedback_points=["All tests passed"], pass_status=True)
    assert good.score == 100
    with pytest.raises(Exception):
        GradeFeedback(score=110, feedback_points=["No"], pass_status=True)


def test_sandbox_fails_closed_when_docker_unavailable(monkeypatch):
    """Block execution of a Sprints submission when Docker is unavailable."""
    monkeypatch.setattr(code_repl.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="refusing unsafe host code execution"):
        code_repl.execute_submission("print('unsafe')", "sum_two")


@pytest.mark.parametrize("sandbox_ready", [False, True])
def test_sandbox_cleans_up_on_startup_or_execution_timeout(monkeypatch, sandbox_ready):
    """Keep Sprints code off an unready sandbox and clean up expired containers."""
    process = MagicMock()
    process.__enter__.return_value = process
    process.poll.return_value = None
    process.returncode = None
    process.communicate.side_effect = subprocess.TimeoutExpired("docker", timeout=3)
    remove_container = Mock()

    def launch(command, *, stdin, stdout, stderr):
        """Provide the grader's ready line only in the execution-timeout case."""
        assert stdin == subprocess.PIPE
        if sandbox_ready:
            stdout.write(code_repl._READY_LINE)
            stdout.flush()
        container_name = command[command.index("--name") + 1]
        remove_container.expected_name = container_name
        return process

    monkeypatch.setattr(code_repl, "SANDBOX_STARTUP_TIMEOUT_SECONDS", 0)
    monkeypatch.setattr(code_repl.shutil, "which", lambda name: "docker")
    monkeypatch.setattr(code_repl.subprocess, "Popen", launch)
    monkeypatch.setattr(code_repl.subprocess, "run", remove_container)

    expected_error = "code execution timed out" if sandbox_ready else "startup timed out"
    with pytest.raises(RuntimeError, match=expected_error):
        code_repl.execute_submission("def sum_two(a, b): return a + b", "sum_two", timeout=3)

    if sandbox_ready:
        process.communicate.assert_called_once()
        assert process.communicate.call_args.kwargs["timeout"] == 3
    else:
        process.communicate.assert_not_called()
    process.kill.assert_called_once()
    assert remove_container.call_args.args[0] == ["docker", "rm", "-f", remove_container.expected_name]


def test_generic_tool_failure_is_structured():
    """Include the failing tool in an unverifiable Sprints result."""
    error = unable_to_verify("sqlite", "connection failed")
    assert error["status"] == "Unable to verify"
    assert error["tool"] == "sqlite"


def test_rubric_contains_explicit_cases():
    """Keep explicit sum_two checks and a pass threshold for the demo Assessor."""
    rubric = code_repl.load_rubric("sum_two")
    assert rubric["pass_threshold"] == 70
    assert len(rubric["tests"]) == 3
