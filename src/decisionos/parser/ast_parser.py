from __future__ import annotations

import ast
from pathlib import Path

from .models import Edge, Node

IGNORED_DIRS = {".git", "__pycache__", ".venv", "venv", "env", "node_modules", ".mypy_cache", ".pytest_cache"}


def find_python_files(repo_root: Path) -> list[Path]:
    return [p for p in repo_root.rglob("*.py") if not any(part in IGNORED_DIRS for part in p.parts)]


def _qualname(class_stack: list[str], name: str) -> str:
    return ".".join([*class_stack, name])


def _module_name_for_file(repo_root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(repo_root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_import_target(module_name: str, module_to_file: dict[str, str]) -> str | None:
    """Resolve a dotted module name to an in-repo file, walking up parent packages."""
    parts = module_name.split(".")
    while parts:
        candidate = ".".join(parts)
        if candidate in module_to_file:
            return module_to_file[candidate]
        parts = parts[:-1]
    return None


def _package_context(module_name: str, is_package: bool) -> str:
    """The package that a single leading dot ('.', level=1) refers to for this module."""
    if is_package:
        return module_name
    parts = module_name.split(".")
    return ".".join(parts[:-1])


def _resolve_relative_import(
    current_module: str, is_package: bool, module: str | None, level: int, names: list[str]
) -> list[str]:
    """Turn a `from .foo import x` / `from . import x` statement into candidate dotted module names."""
    base_parts = _package_context(current_module, is_package).split(".") if current_module else []
    strip = level - 1
    if strip > len(base_parts):
        return []
    target_package = ".".join(base_parts[: len(base_parts) - strip] if strip else base_parts)

    if module:
        return [f"{target_package}.{module}" if target_package else module]

    # `from . import x, y` — each name may itself be a sibling submodule.
    return [f"{target_package}.{name}" if target_package else name for name in names]


class _FileVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.nodes: list[Node] = []
        self.imported_modules: list[str] = []
        self.relative_imports: list[tuple[str | None, int, list[str]]] = []
        self._class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualname = _qualname(self._class_stack, node.name)
        self.nodes.append(
            Node(
                id=f"{self.rel_path}::{qualname}",
                type="class",
                name=node.name,
                file_path=self.rel_path,
                lineno=node.lineno,
                end_lineno=getattr(node, "end_lineno", None),
                docstring=ast.get_docstring(node),
            )
        )
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualname = _qualname(self._class_stack, node.name)
        self.nodes.append(
            Node(
                id=f"{self.rel_path}::{qualname}",
                type="function",
                name=node.name,
                file_path=self.rel_path,
                lineno=node.lineno,
                end_lineno=getattr(node, "end_lineno", None),
                docstring=ast.get_docstring(node),
            )
        )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imported_modules.append(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level == 0:
            if node.module:
                self.imported_modules.append(node.module)
        else:
            names = [alias.name for alias in node.names]
            self.relative_imports.append((node.module, node.level, names))


def parse_repository(repo_root: Path) -> tuple[list[Node], list[Edge]]:
    repo_root = repo_root.resolve()
    py_files = find_python_files(repo_root)

    file_rel_paths: dict[Path, str] = {f: f.relative_to(repo_root).as_posix() for f in py_files}
    module_to_file: dict[str, str] = {_module_name_for_file(repo_root, f): rel for f, rel in file_rel_paths.items()}
    file_to_module: dict[str, str] = {rel: module for module, rel in module_to_file.items()}

    nodes: list[Node] = []
    edges: list[Edge] = []

    for f in py_files:
        rel = file_rel_paths[f]
        nodes.append(Node(id=rel, type="file", name=f.name, file_path=rel))

        try:
            source = f.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel)
        except (SyntaxError, UnicodeDecodeError):
            continue

        visitor = _FileVisitor(rel)
        visitor.visit(tree)
        nodes.extend(visitor.nodes)

        candidate_modules = list(visitor.imported_modules)

        current_module = file_to_module.get(rel, "")
        is_package = f.name == "__init__.py"
        for module, level, names in visitor.relative_imports:
            candidate_modules.extend(_resolve_relative_import(current_module, is_package, module, level, names))

        seen_targets: set[str] = set()
        for module_name in candidate_modules:
            target = _resolve_import_target(module_name, module_to_file)
            if target and target != rel and target not in seen_targets:
                edges.append(Edge(src=rel, dst=target, type="imports"))
                seen_targets.add(target)

    return nodes, edges
