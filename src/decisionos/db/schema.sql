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
