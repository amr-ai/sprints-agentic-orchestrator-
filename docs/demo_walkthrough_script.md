# 3-5 Minute Demo Script (record a real screen capture)

**0:00-0:30 — Setup:** Show `.env` (redacted), `python -m src.main init`, `python -m src.main ingest`, Docker sandbox image and `pytest -q` results. Distinguish the synthetic curriculum and fictional job openings.

**0:30-1:40 — Curriculum query:** Start `python -m src.main shell --learner SPR-1001`. Ask: `How does LangGraph StateGraph route advisor and assessor questions?` Show Chroma source, answer and measured retrieval latency. Follow up with an unrelated unsupported curriculum question and show the explicit unable-to-verify path.

**1:40-2:45 — Python grading:** Enter `/code data/demo_submission.py sum_two`. Show Docker-only PythonREPL execution, test results, typed grade JSON schema and at-most-three judge iterations. Temporarily remove Docker from PATH and demonstrate fail-closed behavior (no host execution).

**2:45-4:00 — Career matching and approval:** First run `python -m src.main seed-demo-jobs` to create **fictional** openings. Ask `Find a placement match for me`. Show the SQL record match, Sprints learner qualifications, tier-1 approval interrupt, explicit reviewer input and resumed graph. Explain this is a DEMO match and not a confirmed Fawry opening.

**4:00-4:30 — Evidence and limits:** Open report and discuss missing official curriculum, 25 rather than 500 learners, missing verified partner vacancies, production auth, persistence and isolated execution limitations.

Never claim that a narrated demo is a recorded MP4. Record an actual 3-5 minute walkthrough after running the project with a valid Gemini key and Docker.
