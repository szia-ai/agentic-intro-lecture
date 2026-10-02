"""
PostToolUse hook for Edit, Write and NotebookEdit: format and lint the edited file with ruff.

Only the edited file is touched (the same scope as the ruff pre-commit hook), so
diffs stay minimal. Findings that `ruff check --fix` cannot fix go back to Claude
as additional context; a clean file stays silent and costs no tokens.
"""

import json
import subprocess
import sys
from pathlib import Path

PYTHON_SUFFIXES = (".py", ".pyi", ".ipynb")
MAX_REPORTED_FINDINGS = 20


def run_ruff(args: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Run ruff from the project environment, or through uvx when it is not installed there.

    Args:
        args: Arguments passed to ruff, e.g. ["format", "src/app.py"].

    Returns:
        The finished process with its exit code, stdout and stderr.

    Example:
        >>> run_ruff(["--version"]).returncode
        0
    """
    result = subprocess.run(
        ["uv", "run", "--no-sync", "ruff", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 2 and "Failed to spawn" in result.stderr:
        result = subprocess.run(
            ["uvx", "ruff", *args], capture_output=True, text=True, check=False
        )
    return result


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(
            f"format_edited_file: could not parse the hook input ({error})",
            file=sys.stderr,
        )
        return 1  # non-blocking: shows a hook error in the transcript
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not file_path.endswith(PYTHON_SUFFIXES) or not Path(file_path).is_file():
        return 0

    try:
        # --- Fix, then format (ruff's recommended order), then report what is left ---
        fix = run_ruff(["check", "--fix", "--quiet", file_path])
        run_ruff(["format", "--quiet", file_path])
        if fix.returncode == 0:
            return 0
        check = run_ruff(["check", "--quiet", "--output-format", "concise", file_path])
    except FileNotFoundError:
        print(
            "format_edited_file: uv is not on PATH, ruff was skipped", file=sys.stderr
        )
        return 1
    if check.returncode == 0:
        return 0
    if (
        check.returncode != 1
    ):  # 2 = ruff itself failed, e.g. a broken [tool.ruff] config
        print(
            f"format_edited_file: ruff failed: {check.stderr.strip()[:500]}",
            file=sys.stderr,
        )
        return 1

    findings = check.stdout.strip().splitlines()
    shown = "\n".join(findings[:MAX_REPORTED_FINDINGS])
    if len(findings) > MAX_REPORTED_FINDINGS:
        shown += f"\n... and {len(findings) - MAX_REPORTED_FINDINGS} more"
    context = (
        f"ruff left {len(findings)} finding(s) in {file_path} after auto-fix. "
        "Fix the ones your edit introduced; list pre-existing ones instead of fixing them.\n"
        f"{shown}"
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
