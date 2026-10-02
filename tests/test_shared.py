"""Tests for the shared parts: seed script, prompts, output models and examples."""

import re
import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from agentic_demo.models import Triage
from agentic_demo.paths import EXAMPLES_PATH, PROMPTS_DIR, QUESTIONS_PATH
from agentic_demo.prompts import load_examples, load_prompt
from mcp_server.server import run_sql

# "revenue" is allowed only as gross/net revenue or as the gross_revenue/net_revenue columns.
BARE_REVENUE = re.compile(
    r"(?<!gross )(?<!net )(?<!gross_)(?<!net_)\brevenue\b", re.IGNORECASE
)


def read_rows(db_path: Path) -> list[tuple[str, str, str, int, float, float]]:
    with closing(sqlite3.connect(db_path)) as connection:
        return connection.execute(
            "SELECT * FROM sales ORDER BY month, region, product"
        ).fetchall()


def test_seed_is_reproducible(
    tmp_path: Path, seed_runner: Callable[[Path, Path], None]
) -> None:
    questions = tmp_path / "questions.yaml"
    questions.write_text(QUESTIONS_PATH.read_text())
    seed_runner(tmp_path / "a.db", questions)
    seed_runner(tmp_path / "b.db", questions)
    rows = read_rows(tmp_path / "a.db")
    assert rows == read_rows(tmp_path / "b.db")
    assert len(rows) == 216
    assert all(re.fullmatch(r"\d{4}-\d{2}", row[0]) for row in rows)
    assert all(row[5] < row[4] for row in rows)
    filled = yaml.safe_load(questions.read_text())
    assert filled[0]["expected"] in {"APAC", "EMEA", "Americas"}
    assert 0 < filled[1]["expected_net"] < filled[1]["expected_gross"]


def test_prompts_load_without_the_version_line() -> None:
    for name in ("basic", "triage", "analyst", "reviewer"):
        assert (PROMPTS_DIR / f"{name}.md").read_text().startswith("PROMPT_VERSION: ")
        text = load_prompt(name)
        assert text and "PROMPT_VERSION" not in text


def test_prompt_without_a_header_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "bad.md").write_text("no header here\n")
    monkeypatch.setattr("agentic_demo.prompts.PROMPTS_DIR", tmp_path)
    with pytest.raises(ValueError, match="PROMPT_VERSION"):
        load_prompt("bad")


def test_triage_accepts_only_the_four_scenarios() -> None:
    triage = Triage(scenario="clarify", question="Gross or net revenue?")
    assert triage.scenario == "clarify"
    with pytest.raises(ValidationError):
        Triage.model_validate({"scenario": "maybe", "question": ""})


@pytest.mark.usefixtures("sales_db")
def test_examples_run_and_always_name_gross_or_net() -> None:
    examples = yaml.safe_load(EXAMPLES_PATH.read_text())
    assert len(examples) == 5
    for example in examples:
        assert run_sql(example["sql"])["rows"], example["question"]
        assert not BARE_REVENUE.search(example["question"] + " " + example["sql"]), (
            example
        )
    assert "Verified examples" in load_examples()
