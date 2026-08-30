from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import config

URL_RE = re.compile(r"^(https?://|git@)")


def _repo_name_from_url(url: str) -> str:
    name = url.rstrip("/").rsplit("/", 1)[-1]
    return name[:-4] if name.endswith(".git") else name


def resolve_repo_source(source: str) -> Path:
    """Accepts a local path or a git URL. URLs are cloned (or updated, if already cloned) under repos/."""
    if not URL_RE.match(source):
        return Path(source)

    dest = config.PROJECT_ROOT / "repos" / _repo_name_from_url(source)
    if dest.exists():
        subprocess.run(["git", "-C", str(dest), "pull", "--ff-only"], check=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", source, str(dest)], check=True)

    return dest
