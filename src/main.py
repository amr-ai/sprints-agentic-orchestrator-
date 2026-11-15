"""Sprints Gemini LangGraph command-line demo: init, ingest and live shell."""
import argparse
import logging
import json
from pathlib import Path
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from src.agents.graph import build_graph
from src.tools.db_queries import initialize_db, seed_demo_openings
from src.tools.rag_retriever import ingest_curriculum


def _render(result):
    if "__interrupt__" in result:
        for item in result["__interrupt__"]:
            print("\nAPPROVAL REQUIRED (HITL):", json.dumps(item.value, indent=2))
        return True
    print("\nASSISTANT:", result.get("answer", "Unable to verify"))
    if result.get("retrieval_ms") is not None:
        print("Retrieval latency (including embeddings) ms:", result["retrieval_ms"])
    if result.get("error"):
        print("Structured failure:", json.dumps(result["error"], indent=2))
    return False


def run_shell(learner_id: str):
    """Maintain MemorySaver context and approval resume in one live process."""
    graph = build_graph()
    config = {"configurable": {"thread_id": f"learner::{learner_id}"}}
    print(f"Sprints Gemini shell | learner={learner_id} | /code PATH ASSIGNMENT_ID | /quit")
    print("This local CLI is a demonstration, not an authenticated placement interface.")
    while True:
        try:
            query = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if query in {"/quit", "/exit"}:
            break
        if not query:
            continue
        code = ""
        assignment_id = "sum_two"
        if query.startswith("/code "):
            try:
                _, file_path, assignment_id = query.split(maxsplit=2)
                code = Path(file_path).read_text(encoding="utf-8")
            except Exception as exc:
                print("Code input error:", exc)
                continue
            query = f"Grade my Python submission for {assignment_id}"
        try:
            result = graph.invoke({"messages": [HumanMessage(content=query)],
                                   "learner_id": learner_id, "query": query,
                                   "submission_code": code, "assignment_id": assignment_id},
                                  config=config)
            interrupted = _render(result)
            if interrupted:
                print("No automatic tier-1 approval. This CLI simulates reviewer identity only.")
                approved = input("Approve this DEMO match? (yes/no): ").lower() == "yes"
                reviewer = input("Reviewer ID (simulation): ").strip()
                resumed = graph.invoke(Command(resume={
                    "approved": approved, "reviewer_id": reviewer,
                }), config=config)
                _render(resumed)
        except Exception as exc:
            print("Unable to verify: Graph execution failed:", str(exc))


def main():
    parser = argparse.ArgumentParser(description="Sprints Gemini multi-agent CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Load the supplied learner CSV into SQLite")
    sub.add_parser("ingest", help="Embed curriculum .md/.txt in persistent Chroma")
    sub.add_parser("seed-demo-jobs", help="Add explicitly fictional demo job openings")
    shell = sub.add_parser("shell", help="Run in-process conversational Graph/HITL demo")
    shell.add_argument("--learner", default="SPR-1001")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if args.command == "init":
        print("Imported learner records:", initialize_db())
    elif args.command == "seed-demo-jobs":
        print("Added FICTIONAL demo vacancies:", seed_demo_openings())
    elif args.command == "ingest":
        print(json.dumps(ingest_curriculum(), indent=2))
    else:
        run_shell(args.learner)


if __name__ == "__main__":
    main()
