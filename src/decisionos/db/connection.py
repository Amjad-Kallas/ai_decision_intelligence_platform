from __future__ import annotations

from pathlib import Path

import duckdb

from .. import config


def get_connection(db_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    db_path = db_path or config.DUCKDB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def init_schema(con: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    con.execute(schema_path.read_text(encoding="utf-8"))


def list_repos(con: duckdb.DuckDBPyConnection | None = None) -> list[str]:
    con = con or get_connection()
    return [row[0] for row in con.execute("SELECT DISTINCT repo FROM nodes ORDER BY repo").fetchall()]
