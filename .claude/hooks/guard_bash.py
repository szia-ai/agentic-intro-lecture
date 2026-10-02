"""
PreToolUse guard for the Bash tool.

Blocks commands that create or publish commits, and commands that would display
secrets: reading or copying a `.env` file, dumping the environment, or printing a
variable whose name looks like a secret. Exit code 2 blocks the call and sends the
reason to Claude; exit code 0 leaves the decision to the normal permission rules.

This checks the command text, so it is a guardrail against accidents, not a
boundary: a glob (`cat .en*`) or an escaped name (`cat \\.env`) gets past it. The
permission deny rules and the sandbox are the enforcement layers.
"""

import json
import re
import sys

# `git [global options] <subcommand>` for subcommands that create or publish commits.
GIT_COMMIT_OR_PUBLISH = re.compile(
    r"\bgit(?:\s+(?:-C\s+\S+|-c\s+\S+|--?[\w-]+(?:=\S+)?))*"
    r"\s+(?:commit|push|merge|rebase|cherry-pick|revert)(?![\w-])"
)

# A `.env` file such as `.env`, `.env.local` or `config/.env`, but not `.env.example`
# and not the regex `\.env` of a code search.
ENV_FILE_PATTERN = (
    r"(?<![\w.\\-])(?:[\w./-]*/)?\.env(?!\.example\b)(?:\.[\w-]+)*(?![\w-])"
)
ENV_FILE = re.compile(ENV_FILE_PATTERN)

# `< .env`, `$(<.env)` or `< ~/.env`: the shell reads the file, whatever the command is.
REDIRECT_FROM_ENV_FILE = re.compile(r"<\s*[^\s;&|<>]*" + ENV_FILE_PATTERN)

# `--exclude=.env`, `--exclude .env`, `--exclude-from=list` and `-x .env` keep the file
# out of an archive or a sync, so they are dropped before matching.
EXCLUDE_OPERAND = re.compile(r"(?:--exclude(?:-from)?[=\s]+|-x\s+)\S+")

# Commands and calls that print or copy a file's contents. `echo` and `printf` are
# not here: they print their arguments, and secret variables are caught separately.
DISPLAY_VERB = re.compile(
    r"\b(?:cat|less|more|head|tail|bat|tac|nl|grep|rg|ag|awk|sed|cut|sort|uniq|"
    r"strings|xxd|od|hexdump|base64|dd(?=\s[^;&|]*\bif=)|diff|cp|rsync|scp|tar|zip|"
    r"print|open|read_text|read_bytes|dotenv_values)\b"
)

# `printenv`, or `env` on its own (not `env VAR=1 command`).
ENV_DUMP = re.compile(r"(?:^|[\s;&|(])(?:printenv\b|env(?=\s*(?:$|[|;&>)])))")

# `echo $OPENAI_API_KEY`, `printf '%s' "${AWS_SECRET_ACCESS_KEY}"` and similar.
SECRET_VARIABLE = re.compile(
    r"\b(?:echo|printf)\b[^;&|]*\$\{?[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*"
)

# `print(os.environ["OPENAI_API_KEY"])`, `print(os.getenv("X_TOKEN"))`,
# `print(os.environ)`, `print(dict(os.environ.items()))` and `print(dotenv_values())`
# on one line; `"OPENAI_API_KEY" in os.environ` and `os.environ["HOME"]` pass.
SECRET_PRINT = re.compile(
    r"\bprint\b[^;&|\n]*(?:"
    r"(?:environ(?:\.get)?\s*[\[(]|getenv\s*\()\s*\\?['\"][A-Z0-9_]*"
    r"(?:KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*"
    r"|(?<!\bin\s)\bos\.environ\b(?!\s*(?:\[|\.get\b))"
    r"|\bos\.environ\s*\.\s*(?:items|keys|values|copy)\b"
    r"|\bdotenv_values\b"
    r")"
)


def block_reason(command: str) -> str | None:
    """
    Return why a Bash command must be blocked, or None when it may proceed.

    Args:
        command: The shell command Claude is about to run.

    Returns:
        A one-line reason for Claude, or None.

    Example:
        >>> block_reason("git status") is None
        True
    """
    command = EXCLUDE_OPERAND.sub("", command)
    if GIT_COMMIT_OR_PUBLISH.search(command):
        return (
            "Git is read-only for Claude in this repo: commit, push, merge, rebase, "
            "cherry-pick and revert are done by hand after the checks. "
            "Leave the changes uncommitted and suggest a commit message instead."
        )
    if REDIRECT_FROM_ENV_FILE.search(command) or (
        ENV_FILE.search(command) and DISPLAY_VERB.search(command)
    ):
        return (
            "This would display or copy a .env file. Code may load .env, but its values "
            "must never be printed. Read .env.example to see which keys exist. "
            "To search the code for the text .env, escape the dot: rg -n '\\.env'."
        )
    if (
        ENV_DUMP.search(command)
        or SECRET_VARIABLE.search(command)
        or SECRET_PRINT.search(command)
    ):
        return (
            "This would print environment variables that may hold secrets. "
            'Check that a secret is set with `test -n "$NAME"` '
            'or `"NAME" in os.environ`, '
            'or print one non-secret variable with `echo "$PATH"`.'
        )
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"guard_bash: could not parse the hook input ({error})", file=sys.stderr)
        return 1  # non-blocking: shows a hook error, the permission rules still apply
    command = (payload.get("tool_input") or {}).get("command") or ""
    reason = block_reason(command)
    if reason is None:
        return 0
    print(f"Blocked by .claude/hooks/guard_bash.py: {reason}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
