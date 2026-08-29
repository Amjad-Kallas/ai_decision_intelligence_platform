from pathlib import Path

from decisionos.parser.ast_parser import parse_repository


def test_parse_repository_extracts_nodes_and_import_edges():
    repo_root = Path(__file__).parent / "fixtures" / "sample_repo"
    nodes, edges = parse_repository(repo_root)

    node_ids = {n.id for n in nodes}
    assert "pkg/a.py" in node_ids
    assert "pkg/b.py" in node_ids
    assert "pkg/a.py::foo" in node_ids
    assert "pkg/a.py::Foo" in node_ids
    assert "pkg/a.py::Foo.bar" in node_ids

    import_edges = [(e.src, e.dst) for e in edges if e.type == "imports"]
    assert ("pkg/b.py", "pkg/a.py") in import_edges
