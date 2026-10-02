# AGENTS.md

Instructions for AI coding agents in this repository. People: start with README.md.

## Project

Teaching demo for an internal lecture on agentic AI: an ask-your-data assistant that answers business
questions from a small synthetic SQLite sales table through a read-only MCP server. It is built in
LangGraph, Pydantic AI 2 and Strands Agents (plus an optional AgentCore bonus), each notebook in the same
three stages: a basic bot, scenarios, then memory, examples and a reviewer. The notebooks are the
deliverable, and each must be explainable in 10–15 minutes, so simplicity beats completeness.
Full spec: `docs/brief.md`.

## Setup (uv, no lock file)

- Python 3.13 or newer. Create the environment once: `uv venv && uv pip install -e ".[dev]"`
- No `uv.lock`: never run `uv sync` or `uv lock`, and run tools with `uv run --no-sync ...`
- New dependency: add it to `pyproject.toml` by hand, then re-run the install line (`uv add` writes a `uv.lock`).
- Secrets live in `.env` (gitignored). Code may load it; never print or copy its values. `.env.example` lists the keys.

## Commands

| Purpose | Command |
| --- | --- |
| Format and lint | `uv run --no-sync ruff format <files> && uv run --no-sync ruff check --fix <files>` |
| Type check | `uv run --no-sync ty check <files>` |
| Unit tests | `uv run --no-sync pytest -x -q --tb=short tests/<test file>` |
| SI tests (few, slower) | `uv run --no-sync pytest -x -q tests/integration` |
| Full suite (once, at the end) | `uv run --no-sync pytest -q` |

## Layout

- `notebooks/` the deliverables; `src/agentic_demo/` shared models, loaders and paths; `mcp_server/` the
  read-only MCP server; `prompts/` versioned prompts; `data/` seed script, questions and examples (the
  generated `*.db` and `memory/` are gitignored); `tests/` pytest, `tests/integration/` SI tests;
  `bonus/agentcore/`; `docs/brief.md`.

## Rules

- Minimal modifications: change only what the task needs. No drive-by refactors, renames or reformatting of untouched code; suggest extras at the end instead.
- Proportionate effort: a small change gets a small check. Make the change, run the one command that shows it works, and report. No probes, research or agents for a one-line or config-only change, and no second check of what one check already showed.
- Git is read-only for agents (status, diff, log). Never commit, push, merge or rebase: commits are made by hand after the checks.
- Work on dummy or synthetic data. Never copy real client data into code, tests, prompts or logs.
- Search with `rg` (it skips gitignored files such as `.env`), not `grep -r`.
- Do not do extra work, keep the scope narrow - develop only what the user asked.

## Done means

- Lint and type checks are clean on the changed files, the targeted tests pass, and SI tests pass if a seam changed.
- Very simple, small tasks should not be tested by the reviewer and verifier agents. Tests are enough there.
- The changed functions were tried with a few realistic and awkward inputs, and the results are reported.
- At most two fix rounds per failure; after that, stop and report what is left.

## Project notes

- Use only the current APIs in `docs/brief.md`; when unsure, check the installed package, not memory.
- Never add `strands-agents[openai|anthropic|litellm]`, `bedrock-agentcore[strands-agents]`,
  `langchain-mcp-adapters` or `bedrock-agentcore-starter-toolkit`: they break the shared environment.
- Notebooks use top-level `await`; never `asyncio.run(...)` or Pydantic AI's `run_sync()` in a cell.
- Prompts live in `prompts/*.md` with a `PROMPT_VERSION` header and load through `load_prompt`;
  output schemas are Pydantic models passed to the framework, never pasted into prompts.
- Before handing back a notebook, run it top to bottom (`jupyter execute`) and save the outputs.
- The local model is `qwen3:8b` on Ollama at `localhost:11434`.
- Notebook runs need network access (model APIs, Ollama) and write Jupyter files in the home folder;
  if the sandbox blocks this, stop and ask, and never change the sandbox settings.
- Memory lives under `data/memory/<framework>/`; each notebook's reset cell deletes only its own folder.
