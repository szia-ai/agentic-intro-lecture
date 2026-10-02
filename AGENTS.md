# AGENTS.md

Instructions for AI coding agents in this repository. People: start with README.md.

## Project

<!-- Two or three sentences: what the repo does, its main entry point, who uses the output. -->

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

- `src/<package>/` core code, `tests/` pytest (`tests/integration/` for SI tests), `examples/` or `notebooks/` for demos only, `docs/`, `data/` (gitignored).

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

<!-- What an agent cannot guess: data sources, required environment variables, external services, slow or flaky tests. -->
