"""Index a Python codebase into Pinecone using NVIDIA NIM embeddings."""
from __future__ import annotations
import hashlib
import time
from pathlib import Path
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from code_helper.config import (PROJECT_ROOT, NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_EMBED_MODEL,
    PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_CLOUD, PINECONE_REGION,
    CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_DIMENSION)

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".idea"}
ALLOWED = {".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"}


def load_document(path: Path) -> str:
    """Stage 1: read a text-based source file from disk."""
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_document(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Stage 2: split text into overlapping character chunks, preferring line boundaries."""
    if not text.strip():
        return []
    chunks, start, length = [], 0, len(text)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            boundary = text.rfind("\n", start + chunk_size // 2, end)
            if boundary <= start:
                boundary = text.rfind(" ", start + chunk_size // 2, end)
            if boundary > start:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(start + 1, end - overlap)
    return chunks


def embed_chunks(client: OpenAI, chunks: list[str]) -> list[list[float]]:
    """Stage 3: embed chunks with NVIDIA NIM; batch requests to limit payload size."""
    vectors = []
    for start in range(0, len(chunks), 16):
        batch = chunks[start:start + 16]
        response = client.embeddings.create(model=NVIDIA_EMBED_MODEL, input=batch, encoding_format="float")
        vectors.extend(item.embedding for item in response.data)
        print(f"  Embedded {min(start + len(batch), len(chunks))}/{len(chunks)} chunks")
    return vectors


def store_in_vector_db(vectors: list[list[float]], chunks: list[str], source: str, index) -> int:
    """Stage 4: upsert embedding vectors and source metadata into Pinecone."""
    records = []
    for i, (vector, chunk) in enumerate(zip(vectors, chunks)):
        identity = hashlib.sha256(f"{source}:{i}:{chunk}".encode("utf-8")).hexdigest()[:32]
        records.append({"id": identity, "values": vector, "metadata": {"source": source, "file_name": source, "chunk": i, "text": chunk}})
    for start in range(0, len(records), 100):
        index.upsert(vectors=records[start:start + 100])
    return len(records)


def iter_source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in ALLOWED:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in {".env", "secrets.json"}:
            continue
        yield path


def ensure_index(pc: Pinecone):
    names = {item.name for item in pc.list_indexes()}
    if PINECONE_INDEX_NAME not in names:
        print(f"Creating Pinecone index '{PINECONE_INDEX_NAME}' ({EMBEDDING_DIMENSION} dimensions, cosine)…")
        pc.create_index(name=PINECONE_INDEX_NAME, dimension=EMBEDDING_DIMENSION, metric="cosine",
                        spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION))
        for _ in range(30):
            desc = pc.describe_index(PINECONE_INDEX_NAME)
            status = getattr(desc, "status", desc.get("status") if isinstance(desc, dict) else None)
            ready = getattr(status, "ready", False) if hasattr(status, "ready") else (status.get("ready", False) if isinstance(status, dict) else False)
            if ready:
                break
            time.sleep(2)
    return pc.Index(PINECONE_INDEX_NAME)


def main() -> None:
    if not NVIDIA_API_KEY:
        raise SystemExit("Missing NVIDIA_API_KEY in .env. Copy .env.example to .env and add your key.")
    if not PINECONE_API_KEY:
        raise SystemExit("Missing PINECONE_API_KEY in .env. Pinecone is required by this assignment.")
    if not PROJECT_ROOT.exists():
        raise SystemExit(f"CODEBASE_PATH does not exist: {PROJECT_ROOT}")
    print("=" * 68 + "\nMULTI-AGENT CODE HELPER — CODEBASE INDEXING\n" + "=" * 68)
    print(f"[1/4] Reading source files from: {PROJECT_ROOT}")
    sources = list(iter_source_files(PROJECT_ROOT))
    if not sources:
        raise SystemExit("No supported source files found under CODEBASE_PATH.")
    docs = []
    for path in sources:
        text = load_document(path)
        for chunk_no, chunk in enumerate(chunk_document(text)):
            docs.append((str(path.relative_to(PROJECT_ROOT)), chunk_no, chunk))
    print(f"[2/4] Split {len(sources)} files into {len(docs)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}).")
    client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = ensure_index(pc)
    total = 0
    grouped = {}
    for source, _, chunk in docs:
        grouped.setdefault(source, []).append(chunk)
    for source, chunks in grouped.items():
        print(f"[3/4] Embedding {source} ({len(chunks)} chunks)…")
        vectors = embed_chunks(client, chunks)
        print(f"[4/4] Saving vectors for {source} to Pinecone…")
        total += store_in_vector_db(vectors, chunks, source, index)
    print(f"\nDONE: indexed {total} chunks from {len(sources)} files into '{PINECONE_INDEX_NAME}'.")
    print("Next: run `adk run code_helper` from this folder.")

if __name__ == "__main__":
    main()
