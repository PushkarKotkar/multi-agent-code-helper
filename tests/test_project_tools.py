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


def test_list_project_files():
    from code_helper.tools.project_tools import list_project_files
    output = list_project_files()
    assert "Project root:" in output
    assert "indexer.py" in output or "config.py" in output


def test_inspect_python_structure():
    from code_helper.tools.project_tools import inspect_python_structure
    output = inspect_python_structure("indexer.py")
    assert "FILE: indexer.py" in output
    assert "IMPORTS:" in output
    assert "SYMBOLS:" in output


def test_get_onboarding_overview():
    from code_helper.tools.project_tools import get_onboarding_overview
    output = get_onboarding_overview()
    assert "Project root:" in output
    assert "Top-level entries:" in output


def test_find_text_in_codebase():
    from code_helper.tools.project_tools import find_text_in_codebase
    assert find_text_in_codebase("   ") == "Provide a non-empty search_text."
    found = find_text_in_codebase("def ", file_extension=".py")
    assert ".py:" in found


def test_config_validation():
    from code_helper.config import validate_ai_config
    problems = validate_ai_config()
    assert isinstance(problems, list)
    assert len(problems) == 0


def test_agent_structure():
    from code_helper.agent import root_agent
    assert root_agent.name == "coordinator"
    sub_agent_names = {a.name for a in root_agent.sub_agents}
    assert sub_agent_names == {"code_searcher", "code_explainer", "architecture_mapper", "onboarding_guide"}
