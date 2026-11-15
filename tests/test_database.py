"""Offline tests use only learner CSV/SQLite and fictional openings."""
from pathlib import Path
from tempfile import TemporaryDirectory
from src.tools.db_queries import initialize_db, seed_demo_openings, get_learner, lookup_openings


def test_import_demo_learner_records():
    with TemporaryDirectory() as d:
        db = Path(d) / "students.db"
        assert initialize_db(db) == 25
        assert get_learner("SPR-1001", db)["name"] == "Demo Learner 01"
        assert get_learner("SPR-9999", db) is None


def test_parameterized_queries_reject_sql_injection():
    with TemporaryDirectory() as d:
        db = Path(d) / "students.db"
        initialize_db(db)
        assert get_learner("SPR-1001' OR 1=1 --", db) is None
        assert get_learner("SPR-1001", db) is not None


def test_matching_does_not_invent_jobs_and_uses_recorded_gates():
    with TemporaryDirectory() as d:
        db = Path(d) / "students.db"
        initialize_db(db)
        assert lookup_openings("SPR-1001", db) == []
        assert seed_demo_openings(db) == 3
        matches = lookup_openings("SPR-1001", db)
        assert len(matches) == 1
        assert matches[0]["opening_id"] == "DEMO-JOB-1"
        assert matches[0]["source_status"] == "DEMO_NOT_VERIFIED"
        # In Progress cannot get a placement recommendation.
        assert lookup_openings("SPR-1005", db) == []
