"""Notebook display helpers."""

from IPython.display import Markdown, display


def show_mermaid(diagram: str) -> None:
    """
    Show a Mermaid diagram as a Markdown output.

    JupyterLab 4.1 or newer renders it natively. VS Code renders it from version 1.121 on
    (older versions need the "Markdown Preview Mermaid Support" extension); without that,
    the Mermaid text is shown instead. No web service is involved.

    Args:
        diagram: Mermaid source, for example from `graph.get_graph().draw_mermaid()`.
    """
    display(Markdown(f"```mermaid\n{diagram}\n```"))
