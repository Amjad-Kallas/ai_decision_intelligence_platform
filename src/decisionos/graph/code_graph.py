from __future__ import annotations

import networkx as nx

from ..db.connection import get_connection


def load_import_graph() -> nx.DiGraph:
    con = get_connection()
    graph: nx.DiGraph = nx.DiGraph()

    for node_id, node_type, name in con.execute("SELECT id, type, name FROM nodes WHERE type = 'file'").fetchall():
        graph.add_node(node_id, type=node_type, name=name)

    for src, dst in con.execute("SELECT src, dst FROM edges WHERE type = 'imports'").fetchall():
        graph.add_edge(src, dst)

    return graph


def dependents_of(graph: nx.DiGraph, file_path: str) -> list[str]:
    """Files that import (directly or transitively) file_path."""
    if file_path not in graph:
        return []
    return list(nx.ancestors(graph, file_path))


def dependencies_of(graph: nx.DiGraph, file_path: str) -> list[str]:
    """Files that file_path imports (directly or transitively)."""
    if file_path not in graph:
        return []
    return list(nx.descendants(graph, file_path))
