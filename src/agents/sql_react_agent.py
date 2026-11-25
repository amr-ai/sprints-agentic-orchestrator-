"""Constrained ReAct learner lookup through one parameterized SQL tool."""
import logging
from langchain.agents import create_agent
from langchain_core.tools import tool
from src.config import chat_model
from src.schemas import unable_to_verify
from src.tools.db_queries import format_learner, get_learner


@tool
def get_sprints_learner_record(learner_id: str) -> str:
    """Read Sprints learner progress, salary target, and preferred employers.

    Args:
        learner_id: An exact learner ID such as SPR-1001. No arbitrary SQL.
    """
    learner = get_learner(learner_id)
    return format_learner(learner) if learner else "Unable to verify: learner not found"


def react_lookup_node(state: dict) -> dict:
    """Run a ReAct tool-call trace, then return deterministically verified SQL data."""
    learner_id = state["learner_id"]
    try:
        agent = create_agent(
            model=chat_model(), tools=[get_sprints_learner_record],
            system_prompt=("You are a Sprints learner-record assistant. Always invoke "
                           "get_sprints_learner_record with the exact provided learner ID. "
                           "Do not invent records or extrapolate qualifications."),
        )
        trace = agent.invoke({"messages": [
            {"role": "user", "content": f"Look up the verified learner record for {learner_id}; "
             f"then answer: {state['query']}"}
        ]})
        # Do not expose model claims without independent SQL confirmation.
        learner = get_learner(learner_id)
        if not learner:
            return {"answer": "Unable to verify: learner not found."}
        messages = trace.get("messages", [])
        logging.getLogger(__name__).info("SQL ReAct trace %s", [getattr(m, "type", "unknown") for m in messages])
        had_tool_result = any(getattr(m, "type", "") == "tool" for m in messages)
        if not had_tool_result:
            return {"answer": "Unable to verify: SQL ReAct agent did not call the database tool."}
        return {"answer": format_learner(learner),
                "tool_trace": [getattr(msg, "type", "unknown") for msg in messages]}
    except Exception as exc:
        return {"error": unable_to_verify("sql_react", str(exc)),
                "answer": "Unable to verify: SQL tool could not validate the student record."}
