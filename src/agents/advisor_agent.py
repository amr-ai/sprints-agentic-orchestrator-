"""Agentic curriculum RAG with a self-reflection edge and bounded rewrite."""
from langchain_core.prompts import ChatPromptTemplate
from src.config import chat_model
from src.schemas import ContextAssessment, Rewrite, unable_to_verify
from src.tools.rag_retriever import search_curriculum

REFLECTION = ChatPromptTemplate.from_messages([
    ("system", """You are a strict evidence checker. Does the supplied context
    clearly answer the exact learner question? If evidence is missing, answer
    sufficient=false. Never use general knowledge outside the context."""),
    ("human", "Question: {query}\nContext: {context}"),
])
REWRITE = ChatPromptTemplate.from_messages([
    ("system", "Rewrite a student question as a compact, retrieval-friendly search query."),
    ("human", "Original question: {query}"),
])
ANSWER = ChatPromptTemplate.from_messages([
    ("system", """You are a Sprints curriculum advisor. Answer ONLY from the
    supplied quoted source extracts. Attribute every claim to the source
    filename. If all sources are synthetic DEMO fixtures, explicitly say that
    it is a demonstration and not official curriculum guidance. Do not invent.
    If no support exists, say 'Unable to verify'."""),
    ("human", "Learner question: {query}\nSource extracts:\n{context}"),
])


def retrieve_node(state: dict) -> dict:
    """Search Chroma with Gemini embeddings while logging query latency."""
    attempts = state.get("rag_attempts", 0) + 1
    try:
        docs, latency = search_curriculum(state.get("search_query") or state["query"])
        return {"evidence": docs, "retrieval_ms": latency, "rag_attempts": attempts}
    except Exception as exc:
        return {"rag_attempts": attempts, "error": unable_to_verify("chroma_retrieval", str(exc)),
                "answer": "Unable to verify: curriculum retrieval unavailable."}


def _context(state: dict) -> str:
    """Format retrieved curriculum excerpts with source names and demo markers."""
    return "\n\n".join(
        f"SOURCE {i+1} [{item['source']}] (demo_only={item['demo_only']}):\n{item['text']}"
        for i, item in enumerate(state.get("evidence") or [])
    )


def reflection_node(state: dict) -> dict:
    """Reject answer generation when context does not support a curriculum claim."""
    if state.get("error") or not state.get("evidence"):
        return {"context_sufficient": False}
    try:
        result = (REFLECTION | chat_model().with_structured_output(
            ContextAssessment, method="json_schema"
        )).invoke({"query": state["query"], "context": _context(state)})
        return {"context_sufficient": result.sufficient}
    except Exception as exc:
        return {"context_sufficient": False,
                "error": unable_to_verify("rag_reflection", str(exc))}


def rewrite_node(state: dict) -> dict:
    """Rephrase the query exactly once when curriculum evidence is insufficient."""
    try:
        result = (REWRITE | chat_model().with_structured_output(
            Rewrite, method="json_schema"
        )).invoke({"query": state["query"]})
        return {"search_query": result.reformulated_query}
    except Exception as exc:
        return {"error": unable_to_verify("rag_rewrite", str(exc))}


def answer_node(state: dict) -> dict:
    """Use only retrieved sources to generate the final learner-facing answer."""
    if state.get("error") or not state.get("context_sufficient"):
        return {"answer": "Unable to verify: the provided curriculum does not support this answer."}
    try:
        result = (ANSWER | chat_model()).invoke(
            {"query": state["query"], "context": _context(state)}
        )
        content = result.content
        answer = content if isinstance(content, str) else " ".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
        return {"answer": answer or "Unable to verify: empty response."}
    except Exception as exc:
        return {"error": unable_to_verify("advisor_gemini", str(exc)),
                "answer": "Unable to verify: the advisor model is unavailable."}
