from __future__ import annotations

from pathlib import Path

import ollama

from .. import config
from ..db.connection import get_connection, init_schema


def embed(text: str) -> list[float]:
    # ollama.embed (not the legacy ollama.embeddings) supports server-side truncation
    # instead of erroring when a chunk exceeds the model's context window.
    response = ollama.embed(model=config.EMBED_MODEL, input=text, truncate=True)
    return response["embeddings"][0]


MAX_SOURCE_CHARS = 2_000  # keeps any single chunk from dominating/overflowing the LLM's context window


def _build_chunk_text(node_type: str, name: str, file_path: str, docstring: str | None, source: str) -> str:
    parts = [f"{node_type} `{name}` in {file_path}"]
    if docstring:
        parts.append(docstring)
    if source:
        if len(source) > MAX_SOURCE_CHARS:
            source = source[:MAX_SOURCE_CHARS] + "\n... (truncated)"
        parts.append(source)
    return "\n\n".join(parts)


def ingest_repository(repo_root: Path) -> int:
    """Embed every function/class node into `code_chunks`. Requires build_codemap.py to have run first."""
    repo_root = repo_root.resolve()
    con = get_connection()
    init_schema(con)
    con.execute("DELETE FROM code_chunks")

    rows = con.execute(
        "SELECT id, type, name, file_path, lineno, end_lineno, docstring FROM nodes WHERE type IN ('function', 'class')"
    ).fetchall()

    file_lines_cache: dict[str, list[str]] = {}
    count = 0
    for node_id, node_type, name, file_path, lineno, end_lineno, docstring in rows:
        if file_path not in file_lines_cache:
            file_lines_cache[file_path] = (repo_root / file_path).read_text(encoding="utf-8").splitlines()
        lines = file_lines_cache[file_path]

        source = "\n".join(lines[lineno - 1 : end_lineno]) if lineno and end_lineno else ""
        if not source and not docstring:
            continue

        text = _build_chunk_text(node_type, name, file_path, docstring, source)
        embedding = embed(text)
        con.execute("INSERT INTO code_chunks VALUES (?, ?, ?, ?)", (node_id, file_path, text, embedding))
        count += 1

    return count
