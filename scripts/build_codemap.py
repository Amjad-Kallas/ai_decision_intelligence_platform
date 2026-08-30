from __future__ import annotations

import argparse

from decisionos import config
from decisionos.db.connection import get_connection, init_schema
from decisionos.parser.ast_parser import parse_repository
from decisionos.repo_source import derive_repo_id, resolve_repo_source


def build(repo_source: str) -> None:
    repo_path = resolve_repo_source(repo_source)
    repo_id = derive_repo_id(repo_source)
    nodes, edges = parse_repository(repo_path)

    con = get_connection()
    init_schema(con)
    con.execute("DELETE FROM edges WHERE repo = ?", [repo_id])
    con.execute("DELETE FROM nodes WHERE repo = ?", [repo_id])

    if nodes:
        con.executemany(
            "INSERT INTO nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(repo_id, n.id, n.type, n.name, n.file_path, n.lineno, n.end_lineno, n.docstring) for n in nodes],
        )
    if edges:
        con.executemany(
            "INSERT INTO edges VALUES (?, ?, ?, ?)",
            [(repo_id, e.src, e.dst, e.type) for e in edges],
        )

    print(f"Parsed {repo_path} as repo '{repo_id}'")
    print(f"  files:     {sum(1 for n in nodes if n.type == 'file')}")
    print(f"  classes:   {sum(1 for n in nodes if n.type == 'class')}")
    print(f"  functions: {sum(1 for n in nodes if n.type == 'function')}")
    print(f"  imports:   {sum(1 for e in edges if e.type == 'imports')}")
    print(f"  calls:     {sum(1 for e in edges if e.type == 'calls')}")
    print(f"Stored in {config.DUCKDB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse a Python repo into the code map DuckDB.")
    parser.add_argument("repo_source", help="Local path or git URL of the repo to analyze")
    args = parser.parse_args()
    build(args.repo_source)
