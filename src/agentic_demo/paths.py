"""Repo-relative paths shared by the notebooks, the MCP server, the seed script and the tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "sales.db"
SERVER_PATH = ROOT / "mcp_server" / "server.py"
QUESTIONS_PATH = ROOT / "data" / "questions.yaml"
EXAMPLES_PATH = ROOT / "data" / "examples.yaml"
PROMPTS_DIR = ROOT / "prompts"
MEMORY_DIR = ROOT / "data" / "memory"
