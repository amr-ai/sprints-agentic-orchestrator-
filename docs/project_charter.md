# Project Charter — Sprints Multi-Agent AI Career & Assessment Orchestrator

## Problem
Manual curriculum support, Python grading and graduate-to-partner matching do not scale with growing learner cohorts.

## Scope
A Gemini-driven unified LangGraph TypedDict StateGraph routes Sprints learner requests to curriculum retrieval, code assessment, learner record lookups, or database-backed career matching. Tier-1 partner matches require an explicit human decision via `interrupt` / `Command(resume=...)`.

## Two non-negotiable constraints
1. Per-student conversational state must be isolated through unique thread IDs and LangGraph checkpoints.
2. Python student submissions must execute only in a constrained sandbox, never in the application process.

## Definition of success
- Advisor answers grounded in indexed curriculum and says 'Unable to verify' otherwise.
- Assessor executes code using Docker-isolated PythonREPL and grades only against explicit tests, with schema-validated feedback and at most 3 judge iterations.
- Career agent matches against SQL records, never invents employer qualifications, and blocks tier-1 final decisions pending human review.
- Retrieve-and-reflect branch demonstrably rewrites insufficient queries with a hard two-attempt retrieval limit.
- Chroma retrieval latency recorded and p95 measured against the 1000 ms requirement (not pre-claimed).
- Report and 3-5 minute end-to-end demo show limitations honestly.

## Starter-asset gaps
- CSV contains 25 records, **not** the advertised 500.
- No official curriculum materials were supplied: bundled `DEMO_SAMPLE_NOT_OFFICIAL.md` is synthetic.
- No genuine partner opening feed was supplied: bundled demo job records are fictional.
- Starter repository URL is not supplied in these files.
- `MemorySaver` is process-local; production must use persistent checkpointing with authentication.

## Risks and mitigations
- Hallucinated matching: deterministic SQL filters, explicit source status, fail-closed absent vacancies.
- Code execution security: isolated Docker, network off, resources constrained; use a hardened microVM-grade runner before production.
- Student isolation: unique thread IDs; add authenticated user-to-thread authorization before deploying to students.
- RAG latency: profile query embeddings separately from Chroma search and cache repeated queries.
- Human approval: local shell demonstration only; connect a permissioned staff review interface before launch.
