"""RAG retrieval tools for finding relevant code passages."""
from __future__ import annotations
from openai import OpenAI
from pinecone import Pinecone
from code_helper.config import (NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_EMBED_MODEL,
    PINECONE_API_KEY, PINECONE_INDEX_NAME, TOP_K)


def rag_search(question: str, top_k: int = TOP_K) -> str:
    """Search indexed source-code chunks and return evidence relevant to a question. Use for code locations, behavior, dependencies, and project onboarding facts."""
    if not NVIDIA_API_KEY:
        return "Search unavailable: set NVIDIA_API_KEY in .env, then run index_codebase.py."
    if not PINECONE_API_KEY:
        return "Search unavailable: set PINECONE_API_KEY in .env, then run index_codebase.py."
    try:
        client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
        response = client.embeddings.create(model=NVIDIA_EMBED_MODEL, input=[question], encoding_format="float")
        vector = response.data[0].embedding
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        result = index.query(vector=vector, top_k=max(1, min(int(top_k), 10)), include_metadata=True)
        matches = getattr(result, "matches", []) or []
        if not matches:
            return "I could not find relevant indexed code. Run `python code_helper/index_codebase.py` and try again."
        lines = []
        for i, match in enumerate(matches, 1):
            meta = getattr(match, "metadata", {}) or {}
            source = meta.get("source") or meta.get("file_name", "unknown file")
            chunk = meta.get("text", "")
            score = getattr(match, "score", None)
            lines.append(f"[{i}] {source} (similarity={score!s})\n{chunk}")
        return "\n\n--- Retrieved evidence ---\n\n".join(lines)
    except Exception as exc:
        return f"RAG search failed ({type(exc).__name__}): {exc}. Check API keys, index dimension (2048), and whether indexing completed."
