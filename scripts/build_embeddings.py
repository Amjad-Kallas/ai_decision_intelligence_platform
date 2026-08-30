from __future__ import annotations

import argparse

from decisionos import config
from decisionos.rag.ingest import ingest_repository
from decisionos.repo_source import resolve_repo_source

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed code chunks for semantic search (run build_codemap.py first).")
    parser.add_argument("repo_source", help="Local path or git URL previously passed to build_codemap.py")
    args = parser.parse_args()

    repo_path = resolve_repo_source(args.repo_source)
    count = ingest_repository(repo_path)
    print(f"Embedded {count} code chunks")
    print(f"Stored in {config.DUCKDB_PATH}")
