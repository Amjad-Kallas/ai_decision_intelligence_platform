from __future__ import annotations

import numpy as np

from ..db.connection import get_connection
from .ingest import embed


def search(query: str, top_k: int = 5) -> list[dict]:
    """Cosine-similarity search over code_chunks, computed in-process (corpus is small enough to skip an ANN index)."""
    query_vec = np.array(embed(query), dtype=np.float32)
    query_vec /= np.linalg.norm(query_vec)

    con = get_connection()
    rows = con.execute("SELECT node_id, file_path, content, embedding FROM code_chunks").fetchall()

    scored = []
    for node_id, file_path, content, embedding in rows:
        vec = np.array(embedding, dtype=np.float32)
        vec /= np.linalg.norm(vec)
        score = float(np.dot(query_vec, vec))
        scored.append({"node_id": node_id, "file_path": file_path, "content": content, "score": score})

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]
