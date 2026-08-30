# DecisionOS — Codebase Intelligence

Ask questions about a Python repository and get answers grounded in the
actual code — not the model's memory. Every answer cites the specific
files and functions it came from, plus the real import relationships
between them.

```
Where is the model trained, and what would be affected if I changed model.py?
```

```
The `train_svm` function is defined in `model.py`. This function trains
an SVM classifier using scikit-learn's SVC...

Dependency info for model.py:
  imported by (directly or transitively): main.py
```

## How it works

```text
Repository (local Python project)
        │
        ▼
  ast-based parser  →  files / functions / classes / import edges
        │
        ▼
   DuckDB (nodes, edges, code_chunks + embeddings)
        │                    │
        ▼                    ▼
  networkx graph        semantic search
  (dependents,           (nomic-embed-text
   impact analysis)       via Ollama)
        │                    │
        └─────────┬──────────┘
                   ▼
          Ollama (qwen2.5:3b)
                   ▼
    Streamlit: answer + dependency context + code evidence
```

Two independent, verifiable pillars feed the model, rather than asking
it to reason over raw source directly:

- **Structural**: the repo is parsed with Python's `ast` module into a
  graph of files and their import relationships, stored in DuckDB and
  queried with `networkx` — "what depends on X" and "what breaks if I
  change X" are exact graph traversals, not guesses.
- **Semantic**: every function and class is embedded (`nomic-embed-text`)
  so free-text questions ("where is X implemented?") retrieve the right
  code even when the wording doesn't match an identifier.

The LLM's job is narrow: given the retrieved evidence and dependency
context, write a grounded answer citing specific files/functions — a
single-pass RAG call, not an autonomous multi-step agent.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com/)
running locally.

```bash
uv sync --extra dev
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

## Usage

```bash
# 1. Parse a local Python repo into the code map
uv run python scripts/build_codemap.py /path/to/some/repo

# 2. Embed its functions/classes for semantic search
uv run python scripts/build_embeddings.py /path/to/some/repo

# 3. Ask it questions
uv run streamlit run src/decisionos/app.py
```

Each `build_codemap.py` run replaces the current code map — V1 holds
one repo at a time.

## Evaluation

`evaluation/questions.yaml` holds ground-truth questions (with expected
evidence/keywords) against the demo repo; `run_eval.py` runs them all
and checks retrieval + answer correctness automatically:

```bash
uv run python evaluation/run_eval.py
```

Currently 8/8 passing, covering four question types: dependency lookups,
impact analysis, semantic "where is X" search, and refusal on questions
the repo has no answer to (checked so the model doesn't hallucinate).

## Project structure

```text
src/decisionos/
├── app.py              # Streamlit UI
├── config.py
├── parser/             # ast-based parsing → files/functions/classes/imports
├── db/                 # DuckDB schema + connection
├── graph/              # networkx traversal over the import graph
├── rag/                # chunking, embedding, semantic search
└── agent/              # retrieval + graph context → LLM answer
scripts/                # build_codemap.py, build_embeddings.py
evaluation/             # ground-truth questions + scoring
tests/                  # parser unit tests + fixtures
```

## Known limitations (V1)

- Only file-level **import** edges are tracked — no function-call
  graph yet, so "what calls this function" isn't answerable
  structurally (only via semantic search over code/docstrings).
- One repo's code map at a time; parsing a new repo replaces the old
  one rather than coexisting with it.
- No support for pointing directly at a GitHub URL — the target must
  already be a local path.
- Answer quality is bounded by a 3B local model; it occasionally
  misattributes which file a function lives in even when the correct
  file is in its own retrieved evidence.
