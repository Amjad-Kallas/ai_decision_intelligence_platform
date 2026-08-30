from decisionos import config
from decisionos.db.connection import get_connection, init_schema, list_repos
from decisionos.graph.code_graph import dependents_of, load_import_graph


def test_two_repos_with_colliding_paths_stay_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DUCKDB_PATH", tmp_path / "test.duckdb")

    con = get_connection()
    init_schema(con)

    # Both repos have a file literally named "a.py" and "b.py" -- same node ids, different repos.
    for repo in ("repo_one", "repo_two"):
        con.execute("INSERT INTO nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [repo, "a.py", "file", "a.py", "a.py", None, None, None])
        con.execute("INSERT INTO nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [repo, "b.py", "file", "b.py", "b.py", None, None, None])
        con.execute("INSERT INTO edges VALUES (?, ?, ?, ?)", [repo, "b.py", "a.py", "imports"])

    assert list_repos(con) == ["repo_one", "repo_two"]

    graph_one = load_import_graph("repo_one")
    graph_two = load_import_graph("repo_two")

    assert dependents_of(graph_one, "a.py") == ["b.py"]
    assert dependents_of(graph_two, "a.py") == ["b.py"]
    assert set(graph_one.nodes) == {"a.py", "b.py"}
    assert set(graph_two.nodes) == {"a.py", "b.py"}
