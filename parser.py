from pathlib import Path
import ast
from collections import Counter

LANGUAGE_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".jsx": "JavaScript", ".java": "Java", ".go": "Go", ".rs": "Rust",
    ".cpp": "C++", ".c": "C", ".h": "C/C++", ".cs": "C#", ".rb": "Ruby",
    ".php": "PHP", ".html": "HTML", ".css": "CSS", ".md": "Markdown",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".sql": "SQL",
    ".sh": "Shell", ".txt": "Text", ".toml": "TOML"
}
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules"}

def _safe_read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def _python_info(source: str):
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"imports": [], "docstring": False, "entry": False, "error": str(exc), "complexity": 0}
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    imports = sorted(set(imports))
    entry = any(isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
                for n in ast.walk(tree))
    complexity = sum(isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)) for n in ast.walk(tree))
    return {
        "imports": imports,
        "docstring": bool(ast.get_docstring(tree)),
        "entry": entry,
        "error": None,
        "complexity": complexity,
    }

def analyze_project(root: Path):
    files = []
    py_sources = {}
    languages = Counter()
    dependencies = set()
    entry_points = []
    documented = 0
    large_files = []
    modules = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(p in IGNORE_DIRS for p in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        lang = LANGUAGE_MAP.get(suffix, "Other")
        languages[lang] += 1
        files.append(rel)
        size = path.stat().st_size
        if size > 250_000:
            large_files.append(f"{rel} ({size // 1024} KB)")
        if suffix == ".py":
            source = _safe_read(path)
            py_sources[rel] = source
            info = _python_info(source)
            dependencies.update(info["imports"])
            documented += int(info["docstring"])
            if info["entry"]:
                entry_points.append(rel)
            modules.append({
                "module": rel,
                "imports": ", ".join(info["imports"]) or "—",
                "complexity_signals": info["complexity"],
                "parse_error": info["error"] or "—"
            })

    external = sorted(d for d in dependencies if d not in {"os","sys","json","re","typing","pathlib","math","datetime","collections","itertools","functools","subprocess","logging","unittest","pytest"})
    test_presence = any(("test" in p.lower() or "tests/" in p.lower()) for p in files)
    py_count = languages.get("Python", 0)
    coverage = (documented / py_count * 100) if py_count else 0

    return {
        "file_count": len(files),
        "python_files": py_count,
        "languages": dict(languages),
        "dependencies": external,
        "entry_points": entry_points,
        "has_tests": test_presence,
        "documentation_coverage": coverage,
        "large_files": large_files,
        "files": files,
        "python_sources": py_sources,
        "modules": modules,
    }

def analyze_pasted_python(source: str):
    info = _python_info(source)
    return {
        "file_count": 1,
        "python_files": 1,
        "languages": {"Python": 1},
        "dependencies": info["imports"],
        "entry_points": ["pasted_code.py"] if info["entry"] else [],
        "has_tests": "test" in source.lower(),
        "documentation_coverage": 100 if info["docstring"] else 0,
        "large_files": [],
        "files": ["pasted_code.py"],
        "python_sources": {"pasted_code.py": source},
        "modules": [{
            "module": "pasted_code.py",
            "imports": ", ".join(info["imports"]) or "—",
            "complexity_signals": info["complexity"],
            "parse_error": info["error"] or "—"
        }],
    }
