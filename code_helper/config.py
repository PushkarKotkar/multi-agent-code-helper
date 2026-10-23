"""Central configuration for the Multi-Agent Code Helper."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = Path(os.getenv("CODEBASE_PATH", "../Naive_RAG")).expanduser().resolve()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "") or os.getenv("NVIDIA_NIM_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_CHAT_MODEL = os.getenv("NVIDIA_CHAT_MODEL", "meta/llama-3.2-11b-vision-instruct")
NVIDIA_EMBED_MODEL = os.getenv("NVIDIA_EMBED_MODEL", "nvidia/nemotron-3-embed-1b")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "code-helper")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
CHUNK_SIZE = max(200, int(os.getenv("CHUNK_SIZE", "700")))
CHUNK_OVERLAP = max(0, min(int(os.getenv("CHUNK_OVERLAP", "120")), CHUNK_SIZE - 1))
TOP_K = max(1, int(os.getenv("TOP_K", "4")))
EMBEDDING_DIMENSION = 2048


def validate_ai_config(require_pinecone: bool = True) -> list[str]:
    """Return configuration problems without exposing secret values."""
    problems = []
    if not NVIDIA_API_KEY:
        problems.append("NVIDIA_API_KEY (or NVIDIA_NIM_API_KEY) is missing from .env")
    if require_pinecone and not PINECONE_API_KEY:
        problems.append("PINECONE_API_KEY is missing from .env")
    return problems
