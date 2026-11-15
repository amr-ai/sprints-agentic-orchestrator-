"""Gemini-only configuration for the Sprints multi-agent orchestrator."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def path_from_env(name: str, default: str) -> Path:
    """Resolve project-local storage paths without relying on the current directory."""
    raw = Path(os.getenv(name, default)).expanduser()
    return raw if raw.is_absolute() else ROOT / raw


def gemini_model():
    """Create the Gemini chat model shared by every Sprints worker agent."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key or key == "PASTE_YOUR_GEMINI_API_KEY":
        raise RuntimeError("Set GOOGLE_API_KEY (or GEMINI_API_KEY) in .env")
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        google_api_key=key,
        temperature=0,
        max_retries=1,
        timeout=45,
    )


def gemini_embeddings():
    """Return Gemini embeddings for the Sprints curriculum knowledge base."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key or key == "PASTE_YOUR_GEMINI_API_KEY":
        raise RuntimeError("Set GOOGLE_API_KEY (or GEMINI_API_KEY) in .env")
    return GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
        google_api_key=key,
    )
