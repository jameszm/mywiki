#!/usr/bin/env python3
"""Static analyzer: extract a ground-truth skeleton from a Python repository.

Walks the repo, parses every .py file with the stdlib ast module, and emits a
skeleton.json describing files, their classes/functions, and the import graph
(internal file->file edges plus external dependencies). No LLM involved —
everything in the output provably exists in the code.

Usage:
    python3 tools/analyze.py <repo_path> [-o skeleton.json]
"""
import argparse
import ast
import json
import sys
from datetime import date
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv",
              "build", "dist", ".tox", ".eggs", "htmlcov"}


def find_py_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def module_name(path: Path, root: Path):
    """Dotted module name, walking up through __init__.py packages."""
    pkg_dir = path.parent
    parts = [path.stem] if path.stem != "__init__" else []
    while (pkg_dir / "__init__.py").exists() and pkg_dir != root.parent:
        parts.insert(0, pkg_dir.name)
        if pkg_dir == root:
            break
        pkg_dir = pkg_dir.parent
    return ".".join(parts) if parts else path.stem


def resolve_relative(current_module: str, is_package: bool, level: int, target: str):
    """Resolve `from ...X import y` to an absolute dotted module name."""
    parts = current_module.split(".")
    if not is_package:
        parts = parts[:-1]  # drop the module's own name to get its package
    if level > 1:
        parts = parts[: len(parts) - (level - 1)]
    if target:
        parts = parts + target.split(".")
    return ".".join(parts)


def analyze_file(path: Path, module: str, is_package: bool):
    src = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return {"error": f"syntax error: {exc}"}, []

    doc = ast.get_docstring(tree)
    classes, functions, raw_imports = [], [], []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append({"name": node.name, "line": node.lineno, "methods": methods})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({"name": node.name, "line": node.lineno})

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                raw_imports.append({"module": alias.name, "name": None, "line": node.lineno})
        elif isinstance(node, ast.ImportFrom):
            target = node.module or ""
            if node.level:
                target = resolve_relative(module, is_package, node.level, target)
            for alias in node.names:
                raw_imports.append({"module": target, "name": alias.name, "line": node.lineno})

    info = {
        "loc": src.count("\n") + 1,
        "doc": (doc.strip().splitlines()[0] if doc else None),
        "classes": classes,
        "functions": functions,
    }
    return info, raw_imports


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None)
    args = ap.parse_args()
    root = args.repo.resolve()
    if not root.is_dir():
        sys.exit(f"error: {root} is not a directory")

    # Pass 1: discover files and build module-name -> file map
    files = {}
    modmap = {}
    for path in find_py_files(root):
        rel = path.relative_to(root).as_posix()
        mod = module_name(path, root)
        files[rel] = {"module": mod, "is_package": path.stem == "__init__",
                      "role": "test" if any("test" in p.lower() for p in Path(rel).parts) else "source"}
        modmap[mod] = rel

    # Pass 2: parse and resolve imports
    edges = {}          # (src_file, dst_file) -> set of imported names
    external = {}       # top-level external package -> set of importing files
    for rel, meta in files.items():
        info, raw_imports = analyze_file(root / rel, meta["module"], meta["is_package"])
        meta.update(info)
        for imp in raw_imports:
            target_mod, name = imp["module"], imp["name"]
            resolved = None
            if name and f"{target_mod}.{name}" in modmap:      # from pkg import submodule
                resolved, name = modmap[f"{target_mod}.{name}"], None
            elif target_mod in modmap:
                resolved = modmap[target_mod]
            else:  # walk up dotted path: import a.b.c may resolve to a.b or a
                probe = target_mod
                while "." in probe and probe not in modmap:
                    probe = probe.rsplit(".", 1)[0]
                if probe in modmap:
                    resolved = modmap[probe]
            if resolved and resolved != rel:
                key = (rel, resolved)
                edges.setdefault(key, set())
                if name:
                    edges[key].add(name)
            elif not resolved:
                top = target_mod.split(".")[0]
                if top and top not in ("__future__",):
                    external.setdefault(top, set()).add(rel)

    skeleton = {
        "meta": {
            "repo_path": str(root),
            "language": "python",
            "generated": date.today().isoformat(),
            "file_count": len(files),
            "source_file_count": sum(1 for f in files.values() if f["role"] == "source"),
        },
        "files": [{"path": rel, **meta} for rel, meta in files.items()],
        "edges": [
            {"source": s, "target": t, "names": sorted(names)}
            for (s, t), names in sorted(edges.items())
        ],
        "external_imports": {
            pkg: sorted(fs) for pkg, fs in sorted(external.items())
            if pkg not in sys.stdlib_module_names
        },
        "stdlib_imports": sorted(
            pkg for pkg in external if pkg in sys.stdlib_module_names
        ),
    }

    out = args.output or (Path.cwd() / "skeleton.json")
    out.write_text(json.dumps(skeleton, indent=2, ensure_ascii=False), encoding="utf-8")

    n_src = skeleton["meta"]["source_file_count"]
    n_int = len(skeleton["edges"])
    print(f"analyzed {len(files)} files ({n_src} source) -> {out}")
    print(f"  internal import edges: {n_int}")
    print(f"  external packages:     {len(external)}")


if __name__ == "__main__":
    main()
