"""Validate bounded feedback/retrieval transitions without Gemini calls."""
from src.agents.guards import _judge_path, _rag_path, _career_path


def test_judge_at_most_three_attempts():
    assert _judge_path({"grading_attempts": 1, "judge_approved": False}) == "refine"
    assert _judge_path({"grading_attempts": 2, "judge_approved": False}) == "refine"
    assert _judge_path({"grading_attempts": 3, "judge_approved": False}) == "output"


def test_rag_bounded_rewrite():
    state = {"rag_attempts": 1, "evidence": [{"text": "x"}], "context_sufficient": False}
    assert _rag_path(state) == "rewrite"
    state["rag_attempts"] = 2
    assert _rag_path(state) == "answer"


def test_tier_one_requires_human_approval():
    assert _career_path({"matched_opening": {"tier_1": 1}}) == "approval"
    assert _career_path({"matched_opening": {"tier_1": 0}}) == "output"
