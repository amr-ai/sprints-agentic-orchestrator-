# DEMONSTRATION MATERIAL ONLY - NOT OFFICIAL SPRINTS CURRICULUM

This synthetic document exists only so the starter demo can prove the retrieval workflow.
Replace it with verified curriculum content before presenting any answers as official.

## LangGraph orchestration demo
A StateGraph expresses a stateful workflow as nodes and edges. A TypedDict can
represent shared graph state. Conditional edges can route learners to an
Advisor Agent for curriculum questions or an Assessor Agent for code grading.
A checkpointer associates conversational state with a thread ID.

## Agentic RAG demo
A retriever searches embedded documents. A reflection step checks whether the
retrieved passage is sufficient. If not, the workflow can rewrite the question
and retrieve again, then return an explicit unable-to-verify response.

## Evaluation demo
A code assessor executes candidate code only within an isolated sandbox,
checks explicit test cases, then produces structured Pydantic feedback. The
human team must inspect and authorize critical decisions.
