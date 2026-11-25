"""Docker-isolated Python REPL adapter for untrusted Sprints coding submissions.

NO host execution fallback exists. Never call PythonREPL in the API worker.
Docker must be available and a sandbox image must be built before use.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from src.config import ROOT

RUBRICS = ROOT / "data" / "rubrics" / "assignments.json"
SANDBOX_STARTUP_TIMEOUT_SECONDS = 60
_READY_LINE = b"sprints-sandbox-ready\n"

# Runner is evaluated only inside the sandbox container, not on the host.
_SANDBOX_RUNNER = r'''
import json, sys
from langchain_experimental.utilities import PythonREPL
print("sprints-sandbox-ready", flush=True)
payload = json.load(sys.stdin)
repl = PythonREPL()
code = payload["code"]
tests = payload["tests"]
# PythonREPL runs inside a no-network, unprivileged, resource-limited container.
setup_output = repl.run(code)
results = []
for test in tests:
    # The expression has been defined by the grader's rubric, not the learner.
    run_code = ("try:\n"
                "    __val = " + test["expression"] + "\n"
                "    print(repr(__val))\n"
                "except Exception as exc:\n"
                "    print(type(exc).__name__ + ': ' + str(exc))\n")
    observed = repl.run(run_code).strip()
    results.append({"expected_repr": repr(test["expected"]), "observed": observed,
                    "passed": observed == repr(test["expected"])})
print(json.dumps({"setup_output": setup_output[-2000:], "tests": results}))
'''


def load_rubric(assignment_id: str) -> dict:
    """Load an explicit assignment specification instead of inventing a rubric."""
    data = json.loads(RUBRICS.read_text(encoding="utf-8"))
    if assignment_id not in data:
        raise ValueError(f"Unknown assignment: {assignment_id}")
    return data[assignment_id]


def _wait_for_sandbox(process: subprocess.Popen, stdout_path: Path) -> bool:
    """Wait for the trusted grader to import PythonREPL before sending learner code."""
    deadline = time.monotonic() + SANDBOX_STARTUP_TIMEOUT_SECONDS
    with stdout_path.open("rb") as output:
        while True:
            output.seek(0)
            if output.readline() == _READY_LINE:
                return True
            if process.poll() is not None:
                return False
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Docker sandbox startup timed out before receiving the submission")
            time.sleep(min(0.05, remaining))


def _remove_failed_sandbox(container_name: str) -> None:
    """Remove the unique Sprints container when its attached CLI fails or is stopped."""
    try:
        subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=4, check=False)
    except (subprocess.SubprocessError, OSError):
        pass  # Auto-removal still applies once the container exits.


def execute_submission(code: str, assignment_id: str, timeout: int | None = None) -> dict:
    """Run student code using PythonREPL only INSIDE a Docker sandbox.

    Docker controls: disabled network, read-only root, no capabilities,
    no-new-privileges, unprivileged UID, CPU/memory/PID budgets and timeout.
    Docker startup has a separate deadline. DOCKER_SANDBOX_TIMEOUT_SECONDS
    controls how long the ready sandbox receives to grade a submission.
    """
    if len(code) > 10000:
        raise ValueError("Submission exceeds 10,000 character limit")
    if not shutil.which("docker"):
        raise RuntimeError("Docker unavailable; refusing unsafe host code execution")
    if timeout is None:
        timeout = int(os.getenv("DOCKER_SANDBOX_TIMEOUT_SECONDS", "8"))
    if timeout <= 0:
        raise ValueError("Docker sandbox timeout must be a positive number of seconds")
    rubric = load_rubric(assignment_id)
    image = os.getenv("DOCKER_SANDBOX_IMAGE", "sprints-python-sandbox:local")
    command = [
        "docker", "run", "--rm", "-i", "--pull=never", "--network", "none", "--read-only",
        "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=32",
        "--memory=192m", "--memory-swap=192m", "--cpus=0.5",
        "--user=65534:65534", "--tmpfs=/tmp:rw,nosuid,noexec,size=16m",
        "--log-driver=none", "--ulimit", "nofile=32:32",
        image, "python", "-I", "-B", "-c", _SANDBOX_RUNNER,
    ]
    payload = json.dumps({"code": code, "tests": rubric["tests"]}).encode()
    with tempfile.TemporaryDirectory(prefix="sprints_sandbox_") as work_dir:
        container_name = Path(work_dir).name
        stdout_path = Path(work_dir) / "stdout"
        command[2:2] = ["--name", container_name]
        with stdout_path.open("w+b") as out, tempfile.TemporaryFile(mode="w+b") as err:
            with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err) as process:
                try:
                    ready = _wait_for_sandbox(process, stdout_path)
                    if ready:
                        process.communicate(input=payload, timeout=timeout)
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError("Sandbox code execution timed out") from exc
                finally:
                    if process.poll() is None:
                        process.kill()
                    if process.returncode != 0:
                        _remove_failed_sandbox(container_name)
            out.seek(0)
            err.seek(0)
            stdout = out.read(30000).decode(errors="replace")
            stderr = err.read(3000).decode(errors="replace")
            if process.returncode != 0:
                raise RuntimeError(f"Sandbox exited {process.returncode}: {stderr[:500]}")
            if not ready:
                raise RuntimeError("Docker sandbox exited before it was ready")
    try:
        reply = json.loads(stdout.strip().splitlines()[-1])
        tests = reply["tests"]
        score = round(100 * sum(bool(t["passed"]) for t in tests) / len(tests))
    except (ValueError, IndexError, KeyError, ZeroDivisionError) as exc:
        raise RuntimeError("Invalid sandbox result; grading aborted") from exc
    return {"status": "verified_in_demo_sandbox", "score": score,
            "passed_tests": sum(t["passed"] for t in tests),
            "total_tests": len(tests), "tests": tests,
            "stdout": reply.get("setup_output", "")[:2000],
            "pass_threshold": rubric["pass_threshold"],
            "rubric_description": rubric["description"]}
