from __future__ import annotations

import argparse
from pathlib import Path

from decisionos import config
from decisionos.rag.ingest import ingest_repository

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed code chunks for semantic search (run build_codemap.py first).")
    parser.add_argument("repo_path", type=Path, help="Path to the local repo previously parsed by build_codemap.py")
    args = parser.parse_args()

    count = ingest_repository(args.repo_path)
    print(f"Embedded {count} code chunks")
    print(f"Stored in {config.DUCKDB_PATH}")
