"""Unified Sprints TypedDict StateGraph and bounded self-correction loops."""
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver as MemorySaver
from langgraph.graph import END, START, StateGraph
from src.state import SprintsState
from src.agents.orchestrator import route_node
from src.agents.advisor_agent import retrieve_node, reflection_node, rewrite_node, answer_node
from src.agents.assessor_agent import run_submission_node, write_feedback_node, judge_node, grade_output_node
from src.agents.career_agent import match_node, human_approval_node, career_output_node
from src.agents.sql_react_agent import react_lookup_node
from src.agents.guards import (
    _intent, _rag_path, _rewrite_path, _assessment_path, _feedback_path, _judge_path, _career_path
)


def close_turn_node(state: SprintsState) -> dict:
    """Append assistant response via the LangChain HumanMessage/AIMessage protocol."""
    return {"messages": [AIMessage(content=state.get("answer") or "Unable to verify.")]}


def build_graph(checkpointer=None):
    """Compile one global StateGraph containing all Sprints worker flows."""
    g = StateGraph(SprintsState)
    g.add_node("router", route_node)
    g.add_node("advisor_retrieve", retrieve_node)
    g.add_node("advisor_reflect", reflection_node)
    g.add_node("advisor_rewrite", rewrite_node)
    g.add_node("advisor_answer", answer_node)
    g.add_node("assessor_run", run_submission_node)
    g.add_node("assessor_feedback", write_feedback_node)
    g.add_node("assessor_judge", judge_node)
    g.add_node("assessor_output", grade_output_node)
    g.add_node("career_match", match_node)
    g.add_node("career_human_review", human_approval_node)
    g.add_node("career_output", career_output_node)
    g.add_node("sql_react", react_lookup_node)
    g.add_node("close_turn", close_turn_node)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", _intent, {
        "advisor": "advisor_retrieve", "assessor": "assessor_run",
        "career": "career_match", "learner_record": "sql_react",
        "error": "close_turn",
    })
    g.add_edge("advisor_retrieve", "advisor_reflect")
    g.add_conditional_edges("advisor_reflect", _rag_path, {
        "answer": "advisor_answer", "rewrite": "advisor_rewrite"})
    g.add_conditional_edges("advisor_rewrite", _rewrite_path, {
        "answer": "advisor_answer", "retrieve": "advisor_retrieve"})
    g.add_edge("advisor_answer", "close_turn")
    g.add_conditional_edges("assessor_run", _assessment_path, {
        "output": "assessor_output", "feedback": "assessor_feedback"})
    g.add_conditional_edges("assessor_feedback", _feedback_path, {
        "output": "assessor_output", "judge": "assessor_judge"})
    g.add_conditional_edges("assessor_judge", _judge_path, {
        "output": "assessor_output", "refine": "assessor_feedback"})
    g.add_edge("assessor_output", "close_turn")
    g.add_conditional_edges("career_match", _career_path, {
        "approval": "career_human_review", "output": "career_output"})
    g.add_edge("career_human_review", "career_output")
    g.add_edge("career_output", "close_turn")
    g.add_edge("sql_react", "close_turn")
    g.add_edge("close_turn", END)
    return g.compile(checkpointer=checkpointer or MemorySaver())
