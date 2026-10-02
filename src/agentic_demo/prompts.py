"""Loaders for the versioned prompts and the verified examples."""

import yaml

from agentic_demo.paths import EXAMPLES_PATH, PROMPTS_DIR


def load_prompt(name: str) -> str:
    """
    Load a prompt from `prompts/<name>.md` without its version header.

    Args:
        name: File name without extension, such as "basic" or "analyst".

    Returns:
        The prompt text after the `PROMPT_VERSION: <n>` line.

    Example:
        >>> load_prompt("basic").startswith("You are")
        True
    """
    header, _, body = (PROMPTS_DIR / f"{name}.md").read_text().partition("\n")
    if not header.startswith("PROMPT_VERSION:"):
        raise ValueError(f"prompts/{name}.md must start with a PROMPT_VERSION line")
    return body.strip()


def load_examples() -> str:
    """
    Render `data/examples.yaml` as a Markdown block to append to the analyst prompt.

    Returns:
        A heading followed by one question and SQL pair per example.
    """
    examples = yaml.safe_load(EXAMPLES_PATH.read_text())
    pairs = [f"Q: {example['question']}\nSQL: {example['sql']}" for example in examples]
    return "\n\nVerified examples of our SQL conventions:\n\n" + "\n\n".join(pairs)
