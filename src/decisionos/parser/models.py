from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Node:
    id: str
    type: str  # "file" | "function" | "class"
    name: str
    file_path: str
    lineno: int | None = None
    end_lineno: int | None = None
    docstring: str | None = None


@dataclass
class Edge:
    src: str
    dst: str
    type: str  # "imports"
