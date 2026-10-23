"""Small offline tests for deterministic utility tools and chunking."""
from pathlib import Path
from code_helper.index_codebase import chunk_document


def test_chunk_document_empty():
    assert chunk_document("   ") == []


def test_chunk_document_preserves_content():
    text = "alpha beta gamma delta epsilon"
    chunks = chunk_document(text, chunk_size=12, overlap=3)
    assert chunks
    joined = " ".join(chunks)
    for word in text.split():
        assert word in joined


def test_chunk_document_short_text():
    assert chunk_document("hello world", chunk_size=50, overlap=5) == ["hello world"]
