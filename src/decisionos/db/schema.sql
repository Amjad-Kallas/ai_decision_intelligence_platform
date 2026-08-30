CREATE TABLE IF NOT EXISTS nodes (
    repo VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    lineno INTEGER,
    end_lineno INTEGER,
    docstring VARCHAR,
    PRIMARY KEY (repo, id)
);

CREATE TABLE IF NOT EXISTS edges (
    repo VARCHAR NOT NULL,
    src VARCHAR NOT NULL,
    dst VARCHAR NOT NULL,
    type VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS code_chunks (
    repo VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    embedding FLOAT[] NOT NULL,
    PRIMARY KEY (repo, node_id)
);
