"""500-token / 50-overlap Gemini embedding ingestion into persistent ChromaDB."""
import time
from pathlib import Path
from src.config import ROOT, path_from_env, gemini_embeddings

CURRICULUM_DIR = ROOT / "data" / "curriculum_docs"
CHROMA_DIR = path_from_env("CHROMA_DIR", "data/chroma")
COLLECTION = "sprints_curriculum"


def vectorstore():
    """Open the Sprints curriculum vector database with Gemini embeddings."""
    from langchain_chroma import Chroma
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=gemini_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def ingest_curriculum(directory: Path = CURRICULUM_DIR) -> dict:
    """Tokenize supported text docs using a maximum 500 token / overlap 50 rule."""
    from langchain_core.documents import Document
    from langchain_text_splitters import TokenTextSplitter
    files = sorted([p for p in directory.rglob("*") if p.suffix.lower() in {".md", ".txt"}])
    if not files:
        raise FileNotFoundError("No .md/.txt curriculum files found; add genuine sources")
    splitter = TokenTextSplitter(encoding_name="cl100k_base", chunk_size=500, chunk_overlap=50)
    docs = []
    for file in files:
        text = file.read_text(encoding="utf-8")
        docs.extend(splitter.split_documents([Document(page_content=text, metadata={
            "source": str(file.relative_to(ROOT)),
            "demo_only": file.name.startswith("DEMO_"),
        })]))
    if not docs:
        raise ValueError("Curriculum files had no text")
    store = vectorstore()
    # Stable IDs make re-ingestion idempotent and avoid duplicate retrieval.
    ids = [f"{doc.metadata['source']}:{idx}" for idx, doc in enumerate(docs)]
    previous = store.get(include=[]).get("ids", [])
    if previous:
        store.delete(ids=previous)  # Avoid stale chunks from prior indexing runs.
    store.add_documents(docs, ids=ids)
    return {"files": len(files), "chunks": len(docs), "sources": [str(f) for f in files]}


def search_curriculum(query: str, k: int = 3) -> tuple[list[dict], float]:
    """Perform measured Chroma retrieval and return source metadata to the advisor."""
    started = time.perf_counter()
    docs = vectorstore().similarity_search(query, k=k)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return [
        {"text": d.page_content, "source": d.metadata.get("source", "unknown"),
         "demo_only": d.metadata.get("demo_only", False)} for d in docs
    ], elapsed_ms
