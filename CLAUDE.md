@AGENTS.md

## Claude Code

- Use plan mode for multi-file or unfamiliar changes; skip it for one-line fixes.
- After a code change, run `/verify` once. Fix what it reports, run it at most once more, then report what is left.
- Before I commit a multi-file change, run the `reviewer` agent and pass on its findings and commit message.
