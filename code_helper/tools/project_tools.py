"""Non-generative project inspection tools; these use plain Python only."""
from __future__ import annotations
import ast
from pathlib import Path
from code_helper.config import PROJECT_ROOT

IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}


def _safe_root() -> Path:
    return PROJECT_ROOT.resolve()


def list_project_files() -> str:
    """List project files relative to the configured project root using plain Python; use to understand the repository layout without AI guessing."""
    root = _safe_root()
    if not root.exists():
        return f"Project root does not exist: {root}"
    found = []
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            found.append(str(path.relative_to(root)))
        if len(found) >= 250:
            found.append("… output capped at 250 files")
            break
    return "Project root: " + str(root) + "\n" + ("\n".join(found) if found else "No files found.")


def inspect_python_structure(file_name: str = "") -> str:
    """Parse Python files with ast and report functions, classes, and imports without executing them; use for architecture and dependency questions."""
    root = _safe_root()
    clean_name = (file_name or "").strip(" '\"`")
    if clean_name:
        target = root / clean_name
        if not target.exists():
            matches = [p for p in root.rglob(Path(clean_name).name) if p.is_file()]
            target = matches[0] if matches else target
        if not target.is_file():
            return f"File '{clean_name}' not found under {root}."
        candidates = [target]
    else:
        candidates = sorted(root.rglob("*.py"))
    report = []
    for path in candidates:
        try:
            resolved = path.resolve()
            if not resolved.is_file() or resolved.suffix != ".py":
                continue
            if any(part in IGNORED_DIRS for part in resolved.parts):
                continue
            tree = ast.parse(resolved.read_text(encoding="utf-8", errors="replace"), filename=str(resolved))
            imports = []
            symbols = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append("." * node.level + (node.module or "") )
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    symbols.append(f"{type(node).__name__} {node.name} (line {node.lineno})")
            report.append(f"FILE: {resolved.relative_to(root)}\nIMPORTS: {', '.join(sorted(set(imports))) or '(none)'}\nSYMBOLS:\n  " + ("\n  ".join(sorted(symbols)) or "(none)"))
        except (OSError, SyntaxError, ValueError) as exc:
            report.append(f"FILE: {file_name or path.name}\nCould not inspect: {exc}")
    return "\n\n".join(report) if report else "No Python files found to inspect."


def get_onboarding_overview() -> str:
    """Return a deterministic first-steps overview from the project files and common entry points; use when a developer asks where to start."""
    root = _safe_root()
    files = []
    for path in sorted(root.iterdir()) if root.exists() else []:
        files.append(("DIR " if path.is_dir() else "FILE ") + path.name)
    readme = root / "README.md"
    readme_note = "README.md exists; read it first for project-specific setup." if readme.exists() else "No README.md found; inspect requirements.txt and entry-point Python files."
    likely = [name for name in ("main.py", "app.py", "agent.py", "indexer.py", "query_pipeline.py", "requirements.txt") if (root / name).exists()]
    return f"Project root: {root}\nTop-level entries:\n" + ("\n".join(files) or "(empty)") + f"\n\n{readme_note}\nLikely starting points: {', '.join(likely) if likely else 'inspect the file listing and imports'}"


def find_text_in_codebase(search_text: str, file_extension: str = ".py") -> str:
    """Find literal text in project files using plain Python without an LLM; use when a user asks for exact strings, variable names, or configuration values."""
    root = _safe_root()
    if not search_text.strip():
        return "Provide a non-empty search_text."
    ext = file_extension if file_extension.startswith(".") else "." + file_extension
    matches = []
    for path in root.rglob("*") if root.exists() else []:
        if not path.is_file() or path.suffix.lower() != ext.lower():
            continue
        if any(part in IGNORED_DIRS for part in path.parts) or path.name == ".env":
            continue
        try:
            for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if search_text.casefold() in line.casefold():
                    matches.append(f"{path.relative_to(root)}:{line_no}: {line.strip()[:240]}")
                    if len(matches) >= 100:
                        matches.append("… results capped at 100 matches")
                        return "\n".join(matches)
        except OSError:
            continue
    return "\n".join(matches) if matches else f"No literal matches for {search_text!r} in *{ext} files."
