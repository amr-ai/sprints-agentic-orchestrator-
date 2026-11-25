"""Chat provider and curriculum embedding configuration for Sprints."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def path_from_env(name: str, default: str) -> Path:
    """Resolve project-local storage paths without relying on the current directory."""
    raw = Path(os.getenv(name, default)).expanduser()
    return raw if raw.is_absolute() else ROOT / raw


def chat_provider() -> str:
    """Return the provider selected for this process."""
    provider = os.getenv("CHAT_PROVIDER", "groq").strip().lower()
    if provider not in {"gemini", "groq"}:
        raise ValueError("Set CHAT_PROVIDER to gemini or groq")
    return provider


def chat_model():
    """Create the shared chat model for the selected provider."""
    if chat_provider() == "groq":
        from langchain_groq import ChatGroq

        key = os.getenv("GROQ_API_KEY")
        if not key or key == "PASTE_YOUR_GROQ_API_KEY":
            raise RuntimeError("Set GROQ_API_KEY in .env to use Groq")
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            api_key=key,
            temperature=0,
            timeout=20,
            max_retries=2,
        )

    from langchain_google_genai import ChatGoogleGenerativeAI
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key or key == "PASTE_YOUR_GEMINI_API_KEY":
        raise RuntimeError("Set GOOGLE_API_KEY (or GEMINI_API_KEY) in .env")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    options = {"temperature": 0, "max_retries": 1, "timeout": 45}
    if model == "gemini-3.5-flash-lite":
        options = {"thinking_level": "minimal", "max_retries": 3, "timeout": 20}
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=key,
        **options,
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
