CREATE TABLE IF NOT EXISTS nodes (
    id VARCHAR PRIMARY KEY,
    type VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    lineno INTEGER,
    end_lineno INTEGER,
    docstring VARCHAR
);

CREATE TABLE IF NOT EXISTS edges (
    src VARCHAR NOT NULL,
    dst VARCHAR NOT NULL,
    type VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS code_chunks (
    node_id VARCHAR PRIMARY KEY,
    file_path VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    embedding FLOAT[] NOT NULL
);
