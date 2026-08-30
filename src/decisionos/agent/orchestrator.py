from __future__ import annotations

import re

import ollama

from .. import config
from ..graph.code_graph import callees_of, callers_of, dependencies_of, dependents_of, load_call_graph, load_import_graph
from ..rag.vector_store import search

FILE_MENTION_RE = re.compile(r"[\w\-/]+\.py\b")

SYSTEM_PROMPT = (
    "You are a codebase intelligence assistant. Answer the user's question about a Python "
    "repository using ONLY the code evidence and dependency information provided below. Be "
    "specific: cite exact file names and function/class names from the evidence. If a "
    "'Dependency info' section is provided, treat the files it lists under 'imported by' as the "
    "direct answer to any question about what depends on, imports, or would be affected by "
    "changing that file — name those files explicitly, don't just discuss the affected code in "
    "the abstract. If a 'Call graph info' section is provided, treat the functions listed under "
    "'called by' as the direct answer to any question about what calls, uses, or invokes that "
    "function, and the functions listed under 'calls' as the direct answer to what that function "
    "calls — name them explicitly. If the evidence doesn't contain enough information to answer "
    "confidently, say so instead of guessing."
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


def _format_call_context(node_id: str, call_graph) -> str:
    calls = callees_of(call_graph, node_id)
    called_by = callers_of(call_graph, node_id)
    return (
        f"Call graph info for {node_id}:\n"
        f"  calls (directly or transitively): {', '.join(calls) if calls else 'none'}\n"
        f"  called by (directly or transitively): {', '.join(called_by) if called_by else 'none'}"
    )


def _resolve_context_file(question: str, graph, chunks: list[dict]) -> str | None:
    """Prefer a file the question explicitly names (if it's actually in the graph) over the top search hit."""
    for match in FILE_MENTION_RE.findall(question):
        if match in graph:
            return match
    return chunks[0]["file_path"] if chunks else None


def _resolve_context_node(question: str, call_graph, chunks: list[dict]) -> str | None:
    """Prefer a function/class the question names explicitly over the top search hit.

    Semantic search can rank a function that merely *mentions* the named target (e.g.
    load_cached_data, which calls load_data) above the target itself, since both are
    topically similar. An exact identifier match in the question is a stronger signal.
    """
    name_to_ids: dict[str, list[str]] = {}
    for node_id, data in call_graph.nodes(data=True):
        name_to_ids.setdefault(data.get("name", ""), []).append(node_id)

    evidence_ids = {c["node_id"] for c in chunks}
    for word in re.findall(r"\w+", question):
        candidates = name_to_ids.get(word)
        if not candidates:
            continue
        return next((n for n in candidates if n in evidence_ids), candidates[0])

    return chunks[0]["node_id"] if chunks else None


def answer_question(question: str, repo_id: str, top_k: int = 5) -> dict:
    chunks = search(question, repo_id, top_k=top_k)
    graph = load_import_graph(repo_id)
    call_graph = load_call_graph(repo_id)

    context_file = _resolve_context_file(question, graph, chunks)
    graph_context = _format_graph_context(context_file, graph) if context_file else ""

    context_node = _resolve_context_node(question, call_graph, chunks)
    call_context = _format_call_context(context_node, call_graph) if context_node and context_node in call_graph else ""

    prompt = (
        f"Question: {question}\n\n"
        f"Code evidence:\n{_format_evidence(chunks)}\n\n"
        f"{graph_context}\n\n"
        f"{call_context}\n"
    )

    response = ollama.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        options={"num_ctx": 8192, "temperature": 0.4},  # default is 0.8; lower reduces run-to-run answer variance
    )

    return {
        "answer": response["message"]["content"],
        "evidence": chunks,
        "graph_context": graph_context,
        "call_context": call_context,
    }
