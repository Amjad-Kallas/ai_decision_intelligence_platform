import subprocess
from pathlib import Path

from decisionos import config
from decisionos.repo_source import resolve_repo_source


def test_local_path_passes_through_untouched(tmp_path):
    local = tmp_path / "myrepo"
    local.mkdir()
    assert resolve_repo_source(str(local)) == Path(local)


def test_clones_a_url_that_is_not_yet_present(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, check: calls.append(cmd))

    result = resolve_repo_source("https://github.com/someuser/myrepo.git")

    assert result == tmp_path / "repos" / "myrepo"
    assert calls == [["git", "clone", "--depth", "1", "https://github.com/someuser/myrepo.git", str(result)]]


def test_pulls_a_url_that_is_already_cloned(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    existing = tmp_path / "repos" / "myrepo"
    existing.mkdir(parents=True)
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, check: calls.append(cmd))

    result = resolve_repo_source("https://github.com/someuser/myrepo.git")

    assert result == existing
    assert calls == [["git", "-C", str(existing), "pull", "--ff-only"]]
