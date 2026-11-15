"""Verified SQL career matching with LangGraph HITL for tier-1 employers."""
from langgraph.types import interrupt
from src.schemas import unable_to_verify
from src.tools.db_queries import get_learner, lookup_openings, format_learner


def learner_record_node(state: dict) -> dict:
    """Retrieve and describe Sprints learner progress from SQLite only."""
    try:
        learner = get_learner(state["learner_id"])
        if not learner:
            return {"answer": "Unable to verify: learner record not found."}
        return {"answer": format_learner(learner)}
    except Exception as exc:
        return {"error": unable_to_verify("sqlite_learner", str(exc)),
                "answer": "Unable to verify: learner database unavailable."}


def match_node(state: dict) -> dict:
    """Compute qualification-based matches from recorded opening constraints."""
    try:
        learner = get_learner(state["learner_id"])
        if not learner:
            return {"answer": "Unable to verify: learner not found.", "matched_opening": None}
        if learner["readiness_status"] != "Ready for Placement":
            return {"answer": "No recommendation: learner is not Ready for Placement.",
                    "matched_opening": None}
        openings = lookup_openings(state["learner_id"])
        if not openings:
            return {"answer": "No supported opening match in the current database; "
                              "no employer qualifications have been invented.",
                    "matched_opening": None}
        return {"matched_opening": openings[0]}
    except Exception as exc:
        return {"error": unable_to_verify("sqlite_matching", str(exc)),
                "answer": "Unable to verify: career database unavailable.",
                "matched_opening": None}


def human_approval_node(state: dict) -> dict:
    """Pause tier-1 recommendations until an explicit reviewer decision arrives."""
    opening = state["matched_opening"]
    decision = interrupt({
        "action": "placement_approval_required", "learner_id": state["learner_id"],
        "opening_id": opening["opening_id"], "employer": opening["employer"],
        "role": opening["role"], "source_status": opening["source_status"],
        "warning": "DEMO source is NOT a confirmed vacancy" if opening["source_status"].startswith("DEMO") else "Verify the partner posting",
    })
    # Resume input must contain a reviewer identity; auth is external in production.
    approved = bool(isinstance(decision, dict) and decision.get("approved") is True
                    and str(decision.get("reviewer_id", "")).strip())
    return {"approval": {"approved": approved,
                         "reviewer_id": str(decision.get("reviewer_id", "")) if isinstance(decision, dict) else ""}}


def career_output_node(state: dict) -> dict:
    """Never assert an actual employer offer for demonstration-only openings."""
    opening = state.get("matched_opening")
    if not opening:
        return {"answer": state.get("answer") or "No verified job match."}
    if opening["tier_1"] and not (state.get("approval") or {}).get("approved"):
        return {"answer": "Partner review rejected; no tier-1 placement recommendation issued."}
    demo = opening["source_status"] != "VERIFIED_PARTNER_RECORD"
    label = "DEMO MATCH ONLY - NOT A REAL JOB OPENING" if demo else "Database-backed candidate match"
    return {"answer": (
        f"{label}: learner {state['learner_id']} -> {opening['employer']} / "
        f"{opening['role']} ({opening['opening_id']}). "
        f"Recorded salary range: {opening['salary_min_egp']}-{opening['salary_max_egp']} EGP. "
        f"Review: {'approved by ' + state['approval']['reviewer_id'] if opening['tier_1'] else 'tier-1 approval not required'}. "
        f"This is a matching recommendation, not a hiring or placement confirmation."
    )}
