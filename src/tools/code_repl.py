"""Docker-isolated Python REPL adapter for untrusted Sprints coding submissions.

NO host execution fallback exists. Never call PythonREPL in the API worker.
Docker must be available and a sandbox image must be built before use.
"""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from src.config import ROOT

RUBRICS = ROOT / "data" / "rubrics" / "assignments.json"

# Runner is evaluated only inside the sandbox container, not on the host.
_SANDBOX_RUNNER = r'''
import json, sys
from langchain_experimental.utilities import PythonREPL
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


def execute_submission(code: str, assignment_id: str, timeout: int = 8) -> dict:
    """Run student code using PythonREPL only INSIDE a Docker sandbox.

    Docker controls: disabled network, read-only root, no capabilities,
    no-new-privileges, unprivileged UID, CPU/memory/PID budgets and timeout.
    No auto-grading is allowed if the sandbox cannot be run.
    """
    if len(code) > 10000:
        raise ValueError("Submission exceeds 10,000 character limit")
    if not shutil.which("docker"):
        raise RuntimeError("Docker unavailable; refusing unsafe host code execution")
    rubric = load_rubric(assignment_id)
    image = os.getenv("DOCKER_SANDBOX_IMAGE", "sprints-python-sandbox:local")
    command = [
        "docker", "run", "--rm", "-i", "--network", "none", "--read-only",
        "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=32",
        "--memory=192m", "--memory-swap=192m", "--cpus=0.5",
        "--user=65534:65534", "--tmpfs=/tmp:rw,nosuid,noexec,size=16m",
        "--log-driver=none", "--ulimit", "nofile=32:32",
        image, "python", "-I", "-B", "-c", _SANDBOX_RUNNER,
    ]
    payload = json.dumps({"code": code, "tests": rubric["tests"]})
    with tempfile.TemporaryDirectory(prefix="sprints_sandbox_") as work_dir:
        cidfile = Path(work_dir) / "container.cid"
        command[2:2] = ["--cidfile", str(cidfile)]
        with tempfile.TemporaryFile(mode="w+b") as out, tempfile.TemporaryFile(mode="w+b") as err:
            try:
                # Only the Docker daemon executes learner code, not this Python process.
                result = subprocess.run(command, input=payload.encode(), stdout=out,
                                        stderr=err, timeout=timeout, check=False)
            except subprocess.TimeoutExpired as exc:
                # A killed Docker CLI may leave its container alive; force cleanup.
                if cidfile.exists():
                    cid = cidfile.read_text(encoding="ascii").strip()
                    if cid:
                        try:
                            subprocess.run(["docker", "rm", "-f", cid],
                                           stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL, timeout=4,
                                           check=False)
                        except (subprocess.SubprocessError, OSError):
                            pass  # The host operator should also monitor orphan containers.
                raise RuntimeError("Sandbox code execution timed out") from exc
            out.seek(0)
            err.seek(0)
            stdout = out.read(30000).decode(errors="replace")
            stderr = err.read(3000).decode(errors="replace")
            if result.returncode != 0:
                raise RuntimeError(f"Sandbox exited {result.returncode}: {stderr[:500]}")
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
