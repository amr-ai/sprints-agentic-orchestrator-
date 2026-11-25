# Verification status · 25 November 2026

## Local checks

- `python -m compileall -q src tests docs data` completed.
- `python -m pytest -q` passed all 12 offline tests on Windows. The retrieval-timing cases reuse one learner thread and verify that the CLI clears retrieval timing after grading and a router error.
- The code, `.env.example`, and the live CLI use Groq `openai/gpt-oss-120b` for chat and Gemini `gemini-embedding-001` for embeddings. Gemini chat is also selectable and defaults to `gemini-3.5-flash-lite`.
- The AST audit found docstrings on all 51 function and class definitions in `src`, including the Pydantic contracts and graph guards. All 19 Python definitions in `tests`, `docs`, and `data` also have docstrings.
- All six code cells in `notebooks/evaluator_optimizer_loop.ipynb` reproduced their saved outputs.

## Current Groq CLI run

A scratch SQLite database imported all 25 supplied CSV records and loaded three fictional openings. A fresh Chroma directory indexed one synthetic curriculum file as one chunk. All four flows ran on learner thread `SPR-1001` using the standard CLI. The sandbox start and execution budget was 40 seconds as configured for the demo.

- **Advisor.** Groq answered a routing question using Chroma evidence, cited `DEMO_SAMPLE_NOT_OFFICIAL.md`, and printed **17,372.10 ms** for the full retrieval call.
- **Assessor.** Docker ran the three public `sum_two` rubric tests. All three passed, producing **100/100** with Groq feedback and a separate review. The previous turn's retrieval timing was cleared.
- **Tier-1 career review.** LangGraph interrupted on the fictional Fawry opening. A simulated reviewer supplied a decision and ID, and the resumed response labeled the opening **DEMO MATCH ONLY**.
- **Learner record.** The Groq ReAct agent emitted a `human → ai → tool → ai` trace. The verified SQLite response included 12 completed modules, a 30,000 EGP salary target, and employer preferences.
- **Grading with Docker unavailable.** A separate CLI process without Docker on its search path returned a structured `Unable to verify` result and withheld the grade.

[Watch the 3:31 narrated Groq capture](sprints_narrated_walkthrough.mp4) or [read the narration](demo_walkthrough_script.md). This verification used the installed Python dependencies and existing Docker image.

## Retrieval latency

The current narrated run measured **17,372.10 ms**. A separate interactive Groq run measured **13,718.24 ms** for the same question. Both include opening the vector store, embedding the query with Gemini, and searching Chroma. Both exceeded the **1,000 ms** full retrieval target.

An earlier benchmark on the same demo material recorded five full retrievals, with a median of **2,130.42 ms**. Warm Chroma searches with an open store and precomputed query vector took **8.48–9.61 ms**.

These measurements cover a single question and deployment environment. Production p95 latency and the discovery call's learner wait-time reduction goal remain unverified.

## Remaining scope limits

The client supplied learner records and a kickoff deck. A pilot requires official curriculum, verified partner vacancies, authenticated reviewers, and durable checkpoints.
