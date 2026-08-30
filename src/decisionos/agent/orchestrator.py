from __future__ import annotations

import re

import ollama

from .. import config
from ..graph.code_graph import dependencies_of, dependents_of, load_import_graph
from ..rag.vector_store import search

FILE_MENTION_RE = re.compile(r"[\w\-/]+\.py\b")

SYSTEM_PROMPT = (
    "You are a codebase intelligence assistant. Answer the user's question about a Python "
    "repository using ONLY the code evidence and dependency information provided below. Be "
    "specific: cite exact file names and function/class names from the evidence. If a "
    "'Dependency info' section is provided, treat the files it lists under 'imported by' as the "
    "direct answer to any question about what depends on, imports, or would be affected by "
    "changing that file — name those files explicitly, don't just discuss the affected code in "
    "the abstract. If the evidence doesn't contain enough information to answer confidently, say "
    "so instead of guessing."
)


def _format_evidence(chunks: list[dict]) -> str:
    blocks = [f"--- {c['node_id']} (similarity {c['score']:.2f}) ---\n{c['content']}" for c in chunks]
    return "\n\n".join(blocks)


def _format_graph_context(file_path: str, graph) -> str:
    deps = dependencies_of(graph, file_path)
    dependents = dependents_of(graph, file_path)
    return (
        f"Dependency info for {file_path}:\n"
        f"  imports (directly or transitively): {', '.join(deps) if deps else 'none'}\n"
        f"  imported by (directly or transitively): {', '.join(dependents) if dependents else 'none'}"
    )


def _resolve_context_file(question: str, graph, chunks: list[dict]) -> str | None:
    """Prefer a file the question explicitly names (if it's actually in the graph) over the top search hit."""
    for match in FILE_MENTION_RE.findall(question):
        if match in graph:
            return match
    return chunks[0]["file_path"] if chunks else None


def answer_question(question: str, top_k: int = 5) -> dict:
    chunks = search(question, top_k=top_k)
    graph = load_import_graph()

    context_file = _resolve_context_file(question, graph, chunks)
    graph_context = _format_graph_context(context_file, graph) if context_file else ""

    prompt = f"Question: {question}\n\nCode evidence:\n{_format_evidence(chunks)}\n\n{graph_context}\n"

    response = ollama.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        options={"num_ctx": 8192},
    )

    return {
        "answer": response["message"]["content"],
        "evidence": chunks,
        "graph_context": graph_context,
    }
