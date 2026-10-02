---
name: verify
description: Bounded check of the current Python change - lint, types, targeted pytest, input probes and a few SI tests - ending in a short report. Use after implementing a change and before calling it done, or when the user types /verify.
context: fork
agent: verifier
background: false
allowed-tools: Bash(uv run --no-sync python *)
---

# Verify the current change

Goal: find the errors this change introduced, cheaply. This is not a full QA pass.

## Scope

- Only the uncommitted change: run `git status --short` and `git diff --stat`, then read the changed files.
- Use the commands in the "Commands" section of `AGENTS.md`. Keep output short: `-q`, `-x`, `--tb=short`.

## Ladder

1. **Lint**: `uv run --no-sync ruff check <changed files>`
2. **Types**: `uv run --no-sync ty check <changed files>`
3. **Targeted tests**: `uv run --no-sync pytest -x -q --tb=short <test files covering the changed modules>`
4. **Input probes**: call each changed public function 3-5 times with a typical input, an empty one, `None` or a missing field, a boundary value (0, negative, very large) and a malformed or wrong-type one. For text that reaches an LLM, add a very long, a non-English and an instruction-like input. Run them inline with `uv run --no-sync python - <<'EOF' ... EOF` and create no files. For a pure function with a clear invariant (round-trip, idempotence), one Hypothesis property with `max_examples=50` is a cheap extra, if Hypothesis is already a dev dependency.
5. **SI tests**: only if the change touches a seam (file or network I/O, an API or LLM call, another module's contract): `uv run --no-sync pytest -x -q tests/integration`, or one end-to-end run on dummy data. At most three.
6. **Full suite**: once, and only if steps 1-5 passed: `uv run --no-sync pytest -q`

Steps 1-3 always run. Steps 4-6 run only when step 3 passed.

## Budget

- Run each command at most twice. Do not fix and retry: report, and the main session fixes.
- Stop when the ladder is done or after 15 turns, whichever comes first.
- Findings on lines this change did not touch are pre-existing: list them separately, not as failures.

## Report (at most 15 lines)

- One line per step: PASS, FAIL or SKIPPED (why), with the command used.
- Per failure: `file:line - error - likely cause - smallest fix`.
- Probes: `input -> result -> OK or unexpected`.
- Pre-existing issues, if any, on one line.

Never print environment variables, `.env` contents or other secrets.
