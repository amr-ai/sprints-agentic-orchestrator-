"""Validate bounded feedback/retrieval transitions without Gemini calls."""
import pytest
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda

from src.agents import advisor_agent, assessor_agent, graph as graph_module, orchestrator
from src.agents.guards import _judge_path, _rag_path, _career_path
from src.main import _render
from src.schemas import RouteDecision


def test_judge_at_most_three_attempts():
    """Cap the Sprints rubric feedback loop at three attempts."""
    assert _judge_path({"grading_attempts": 1, "judge_approved": False}) == "refine"
    assert _judge_path({"grading_attempts": 2, "judge_approved": False}) == "refine"
    assert _judge_path({"grading_attempts": 3, "judge_approved": False}) == "output"


def test_rag_bounded_rewrite():
    """Allow only one rewrite after the Sprints Advisor's first search."""
    state = {"rag_attempts": 1, "evidence": [{"text": "x"}], "context_sufficient": False}
    assert _rag_path(state) == "rewrite"
    state["rag_attempts"] = 2
    assert _rag_path(state) == "answer"


def test_tier_one_requires_human_approval():
    """Route tier-1 Sprints partner matches through staff review."""
    assert _career_path({"matched_opening": {"tier_1": 1}}) == "approval"
    assert _career_path({"matched_opening": {"tier_1": 0}}) == "output"


@pytest.mark.parametrize("next_intent", ["assessor", "error"])
def test_retrieval_latency_is_scoped_to_the_current_turn(monkeypatch, capsys, next_intent):
    """Keep learner history while clearing the Advisor timing on later turns."""
    class AdvisorRouter:
        """Stand in for Gemini when routing the first Sprints learner question."""

        def with_structured_output(self, schema, *, method):
            """Supply a typed Advisor routing decision without a network request."""
            return RunnableLambda(lambda _: RouteDecision(intent="advisor"))

    def unavailable(*args):
        """Simulate a Sprints tool or model that cannot verify the request."""
        raise RuntimeError("Unavailable in this test")

    monkeypatch.setattr(orchestrator, "chat_model", AdvisorRouter)
    monkeypatch.setattr(advisor_agent, "search_curriculum", lambda _: ([], 87.5))
    monkeypatch.setattr(assessor_agent, "execute_submission", unavailable)
    graph = graph_module.build_graph()
    config = {"configurable": {"thread_id": "learner::SPR-1001"}}
    query = "How does StateGraph route curriculum questions?"
    first = graph.invoke({"query": query, "messages": [HumanMessage(content=query)]}, config)
    assert first["retrieval_ms"] == 87.5
    _render(first)
    assert "Retrieval latency (including embeddings) ms: 87.5" in capsys.readouterr().out

    monkeypatch.setattr(orchestrator, "chat_model", unavailable)
    code = "def add(a, b): return a + b" if next_intent == "assessor" else ""
    query = "Grade my Python submission"
    second = graph.invoke({"query": query, "submission_code": code,
                           "messages": [HumanMessage(content=query)]}, config)
    assert second["intent"] == next_intent
    assert second["retrieval_ms"] is None
    assert len(second["messages"]) == 4
    if next_intent == "assessor":
        assert "sandbox grading unavailable; no grade awarded" in second["answer"]
    _render(second)
    assert "Retrieval latency" not in capsys.readouterr().out
