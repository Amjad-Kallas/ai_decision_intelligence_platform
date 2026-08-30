# DecisionOS — Codebase Intelligence

Ask questions about a Python repository and get answers grounded in the
actual code — not the model's memory. Every answer cites the specific
files and functions it came from, plus the real import and call
relationships between them. Multiple repos can be parsed and queried
independently, side by side.

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
Repository (local path or GitHub URL)
        │
        ▼
  ast-based parser  →  files / functions / classes / import edges / call edges
        │
        ▼
   DuckDB (nodes, edges, code_chunks + embeddings — tagged per repo)
        │                    │
        ▼                    ▼
  networkx graphs       semantic search
  (import graph +        (nomic-embed-text
   call graph)            via Ollama)
        │                    │
        └─────────┬──────────┘
                   ▼
          Ollama (qwen2.5:3b)
                   ▼
    Streamlit: answer + dependency/call context + code evidence
```

Two independent, verifiable pillars feed the model, rather than asking
it to reason over raw source directly:

- **Structural**: the repo is parsed with Python's `ast` module into a
  graph of files and their import relationships, plus a second graph of
  function/method call relationships — both stored in DuckDB and
  queried with `networkx`. "What depends on X", "what breaks if I
  change X", "what calls X", and "what does X call" are exact graph
  traversals, not guesses.
- **Semantic**: every function and class is embedded (`nomic-embed-text`)
  so free-text questions ("where is X implemented?") retrieve the right
  code even when the wording doesn't match an identifier.

The LLM's job is narrow: given the retrieved evidence and dependency/call
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
# 1. Parse a repo into the code map — local path or GitHub URL
uv run python scripts/build_codemap.py /path/to/some/repo
uv run python scripts/build_codemap.py https://github.com/someuser/somerepo.git

# 2. Embed its functions/classes for semantic search (same argument as step 1)
uv run python scripts/build_embeddings.py /path/to/some/repo

# 3. Ask it questions — pick which parsed repo to query from a dropdown
uv run streamlit run src/decisionos/app.py
```

Every stored row is tagged with a repo identifier (the repo's directory
name, or the name derived from a GitHub URL), so parsing a new repo
does not erase previously-parsed ones — they coexist in the same
DuckDB file and are queried independently.

## Evaluation

`evaluation/questions.yaml` holds ground-truth questions (with expected
evidence/keywords) against the demo repo; `run_eval.py` runs them all
and checks retrieval + answer correctness automatically:

```bash
uv run python evaluation/run_eval.py
```

Currently 9/10 passing (the one failure was reproduced as model
sampling variance on repeat, not a systematic bug), covering five
question types: dependency lookups, impact analysis, call-graph
lookups, semantic "where is X" search, and refusal on questions the
repo has no answer to (checked so the model doesn't hallucinate).

## Project structure

```text
src/decisionos/
├── app.py              # Streamlit UI (repo picker + Q&A)
├── config.py
├── repo_source.py       # resolves a local path or GitHub URL to a repo_id + local path
├── parser/             # ast-based parsing → files/functions/classes/imports/calls
├── db/                 # DuckDB schema + connection (all tables keyed by repo)
├── graph/              # networkx traversal over the import graph and the call graph
├── rag/                # chunking, embedding, semantic search
└── agent/              # retrieval + graph/call context → LLM answer
scripts/                # build_codemap.py, build_embeddings.py
evaluation/             # ground-truth questions + scoring
tests/                  # parser + repo_source unit tests, fixtures
```

## Known limitations

- Call-graph and import-graph resolution is best-effort static analysis
  (no type inference) — dynamic dispatch, `getattr`-based calls, and
  deeply nested/aliased imports may be missed.
- Answer quality is bounded by a 3B local model; it occasionally
  misattributes details or omits one of several correct facts even
  when they're present in its own retrieved evidence — a documented,
  recurring characteristic of this model size rather than a pipeline
  bug (a `qwen2.5:7b-instruct-q4_0` fallback was tested and works, but
  showed no clear accuracy win and ~2x the latency on this GPU, so the
  3B model remains the default).
- No UI to trigger cloning/parsing a new repo from within Streamlit —
  `build_codemap.py`/`build_embeddings.py` must be run first.
