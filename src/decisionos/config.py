from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", PROJECT_ROOT / "data" / "codemap.duckdb"))
TARGET_REPO_PATH = os.getenv("TARGET_REPO_PATH")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
