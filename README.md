# agentic-intro-lecture

An ask-your-data assistant for an internal lecture on agentic AI. A business user asks a question
about a small synthetic sales table in plain English, and an agent reads the schema, writes SQL, runs
it through a read-only MCP server and answers together with its SQL. The same assistant is built in
LangGraph, Pydantic AI 2 and Strands Agents, each in three stages: a basic bot, scenarios, then
memory, examples and a reviewer.

## Setup

```bash
uv venv --python 3.13
uv pip install -e ".[dev]"
uv run --no-sync python -m ipykernel install --user --name agentic-demo   # one kernel for all notebooks
cp .env.example .env                                                       # then fill in the keys
ollama pull qwen3:8b                                                       # local model for stage 3
```

No lock file: never run `uv lock` or `uv sync`.

## Run

```bash
uv run --no-sync jupyter lab
```

Go through the notebooks in order: `00_setup_check`, `01_langgraph`, `02_pydantic_ai`,
`03_strands_agentcore`.

## Checks

```bash
uv run --no-sync ruff format . && uv run --no-sync ruff check --fix .
uv run --no-sync ty check
uv run --no-sync pytest -q
```

## Layout

`AGENTS.md` describes the folders; `docs/brief.md` is the full specification.
