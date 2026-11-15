"""Parameterized SQL tools for the Sprints learner and partner-opening records.

Only approved SELECT queries can be executed; Gemini cannot generate executable SQL.
An optional, separately flagged DEMO job-opening table never implies a real vacancy.
"""
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from contextlib import closing
from src.config import ROOT, path_from_env

DB = path_from_env("SQLITE_DB_PATH", "data/sprints.sqlite3")
LEARNERS_CSV = ROOT / "data" / "sprints_learner_db.csv"
DEMO_JOBS_CSV = ROOT / "data" / "job_openings_demo.csv"


def initialize_db(db_path: Path = DB, csv_path: Path = LEARNERS_CSV) -> int:
    """Import supplied Sprints learner rows into a queryable local SQLite DB."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as con, con:
        con.execute("""CREATE TABLE IF NOT EXISTS learners (
            learner_id TEXT PRIMARY KEY, name TEXT NOT NULL, bootcamp_track TEXT NOT NULL,
            completed_modules INTEGER NOT NULL, python_assignment_score INTEGER NOT NULL,
            target_salary_egp INTEGER NOT NULL, preferred_employers TEXT NOT NULL,
            readiness_status TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS job_openings (
            opening_id TEXT PRIMARY KEY, employer TEXT NOT NULL, role TEXT NOT NULL,
            track TEXT NOT NULL, min_modules INTEGER NOT NULL,
            min_python_score INTEGER NOT NULL, salary_min_egp INTEGER NOT NULL,
            salary_max_egp INTEGER NOT NULL, tier_1 INTEGER NOT NULL,
            source_status TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        with open(csv_path, encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        keys = (
            "learner_id", "name", "bootcamp_track", "completed_modules",
            "python_assignment_score", "target_salary_egp", "preferred_employers",
            "readiness_status"
        )
        con.executemany(
            "INSERT OR REPLACE INTO learners VALUES (?,?,?,?,?,?,?,?)",
            [tuple(row[k] for k in keys) for row in rows],
        )
        return len(rows)


def seed_demo_openings(db_path: Path = DB, csv_path: Path = DEMO_JOBS_CSV) -> int:
    """Explicitly load fictional openings; never label these as employer-confirmed."""
    with open(csv_path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with closing(sqlite3.connect(db_path)) as con, con:
        con.executemany("INSERT OR REPLACE INTO job_openings VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
            (
                r["opening_id"], r["employer"], r["role"], r["track"],
                int(r["min_modules"]), int(r["min_python_score"]),
                int(r["salary_min_egp"]), int(r["salary_max_egp"]),
                int(r["tier_1"]), "DEMO_NOT_VERIFIED",
                datetime.now(timezone.utc).isoformat(),
            ) for r in rows
        ])
    return len(rows)


def _read_con(db_path: Path):
    """Open the learner DB in read-only mode, prohibiting worker writes."""
    return sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True, timeout=2)


def get_learner(learner_id: str, db_path: Path = DB) -> dict | None:
    """Fetch only the requested learner's verified CSV-backed progress and salary."""
    with closing(_read_con(db_path)) as con:
        con.row_factory = sqlite3.Row
        row = con.execute("""SELECT learner_id, name, bootcamp_track,
            completed_modules, python_assignment_score, target_salary_egp,
            preferred_employers, readiness_status FROM learners
            WHERE learner_id = ?""", (learner_id,)).fetchone()
    return dict(row) if row else None


def lookup_openings(learner_id: str, db_path: Path = DB) -> list[dict]:
    """Deterministic matching against recorded requirements, not LLM guesses.

    Only learner track, modules, assessment score, employer preferences, and
    the recorded salary bands can be checked with this starter dataset.
    """
    learner = get_learner(learner_id, db_path)
    if not learner or learner["readiness_status"] != "Ready for Placement":
        return []
    preferred = {s.strip().casefold() for s in learner["preferred_employers"].split(",")}
    with closing(_read_con(db_path)) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""SELECT opening_id, employer, role, track,
            min_modules, min_python_score, salary_min_egp, salary_max_egp,
            tier_1, source_status, updated_at FROM job_openings
            WHERE track = ? AND min_modules <= ? AND min_python_score <= ?
              AND salary_max_egp >= ? ORDER BY salary_max_egp DESC, opening_id ASC""", (
            learner["bootcamp_track"], learner["completed_modules"],
            learner["python_assignment_score"], learner["target_salary_egp"]
        )).fetchall()
    return [dict(r) for r in rows if r["employer"].casefold() in preferred]


def format_learner(learner: dict) -> str:
    """Format only SQL verified facts, avoiding hallucinated qualifications."""
    return (
        f"{learner['name']} ({learner['learner_id']}) | Track: {learner['bootcamp_track']} | "
        f"Completed modules: {learner['completed_modules']} | "
        f"Python score: {learner['python_assignment_score']} | "
        f"Salary target: {learner['target_salary_egp']} EGP | "
        f"Preferred employers: {learner['preferred_employers']} | "
        f"Status: {learner['readiness_status']}"
    )
