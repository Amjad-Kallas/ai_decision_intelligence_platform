from __future__ import annotations

import argparse
from pathlib import Path

from decisionos import config
from decisionos.db.connection import get_connection, init_schema
from decisionos.parser.ast_parser import parse_repository


def build(repo_path: Path) -> None:
    nodes, edges = parse_repository(repo_path)

    con = get_connection()
    init_schema(con)
    con.execute("DELETE FROM edges")
    con.execute("DELETE FROM nodes")

    con.executemany(
        "INSERT INTO nodes VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(n.id, n.type, n.name, n.file_path, n.lineno, n.end_lineno, n.docstring) for n in nodes],
    )
    con.executemany(
        "INSERT INTO edges VALUES (?, ?, ?)",
        [(e.src, e.dst, e.type) for e in edges],
    )

    print(f"Parsed {repo_path}")
    print(f"  files:     {sum(1 for n in nodes if n.type == 'file')}")
    print(f"  classes:   {sum(1 for n in nodes if n.type == 'class')}")
    print(f"  functions: {sum(1 for n in nodes if n.type == 'function')}")
    print(f"  imports:   {len(edges)}")
    print(f"Stored in {config.DUCKDB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse a Python repo into the code map DuckDB.")
    parser.add_argument("repo_path", type=Path, help="Path to the local repo to analyze")
    args = parser.parse_args()
    build(args.repo_path)
