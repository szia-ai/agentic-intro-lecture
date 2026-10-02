"""Shared fixtures: the seeded database and a runner for the seed script."""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from agentic_demo.paths import DB_PATH, QUESTIONS_PATH, ROOT

SEED_SCRIPT = ROOT / "data" / "seed.py"


def run_seed(db_path: Path, questions_path: Path) -> None:
    """Run data/seed.py as a subprocess, writing the database and the filled questions file."""
    command = [
        sys.executable,
        str(SEED_SCRIPT),
        "--db",
        str(db_path),
        "--questions",
        str(questions_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


@pytest.fixture
def seed_runner() -> Callable[[Path, Path], None]:
    return run_seed


@pytest.fixture(scope="session")
def sales_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build data/sales.db once per session; the filled questions go to a temp copy, not the repo file."""
    questions_copy = tmp_path_factory.mktemp("seed") / "questions.yaml"
    questions_copy.write_text(QUESTIONS_PATH.read_text())
    run_seed(DB_PATH, questions_copy)
    return DB_PATH
