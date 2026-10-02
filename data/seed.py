"""Build data/sales.db from a fixed seed and write the expected answers into questions.yaml."""

import argparse
import random
import sqlite3
from contextlib import closing
from pathlib import Path

import yaml

from agentic_demo.paths import DB_PATH, QUESTIONS_PATH

SEED = 42
MONTHS = [
    f"{2024 + (9 + i) // 12}-{(9 + i) % 12 + 1:02d}" for i in range(24)
]  # 2024-10 .. 2026-09
REGION_WEIGHT = {"APAC": 0.8, "EMEA": 1.0, "Americas": 1.3}
LIST_PRICE = {"Basic": 49.0, "Pro": 149.0, "Enterprise": 499.0}

CREATE_TABLE = """CREATE TABLE sales (
    month TEXT NOT NULL,
    region TEXT NOT NULL,
    product TEXT NOT NULL,
    units INTEGER NOT NULL,
    gross_revenue REAL NOT NULL,
    net_revenue REAL NOT NULL
)"""

# Keys match the fields of data/questions.yaml that seed.py fills in.
EXPECTED_SQL = {
    "expected": (
        "SELECT region FROM sales WHERE month BETWEEN '2025-01' AND '2025-12' "
        "GROUP BY region ORDER BY SUM(units) DESC LIMIT 1"
    ),
    "expected_gross": (
        "SELECT ROUND(SUM(gross_revenue)) FROM sales "
        "WHERE region = ? AND month BETWEEN '2026-04' AND '2026-06'"
    ),
    "expected_net": (
        "SELECT ROUND(SUM(net_revenue)) FROM sales "
        "WHERE region = ? AND month BETWEEN '2026-04' AND '2026-06'"
    ),
}

Row = tuple[str, str, str, int, float, float]


def build_rows(seed: int = SEED) -> list[Row]:
    """
    Generate the 216 sales rows (24 months x 3 regions x 3 products) from a fixed seed.

    Args:
        seed: Seed of the random generator; the same seed always gives the same rows.

    Returns:
        Rows of (month, region, product, units, gross_revenue, net_revenue).
    """
    generator = random.Random(seed)
    rows: list[Row] = []
    for month in MONTHS:
        for region, weight in REGION_WEIGHT.items():
            for product, price in LIST_PRICE.items():
                units = int(generator.randint(20, 400) * weight)
                gross = units * price
                discount = generator.uniform(0.05, 0.15)
                returns = generator.uniform(0.01, 0.04)
                net = gross * (1 - discount) * (1 - returns)
                rows.append(
                    (month, region, product, units, round(gross, 2), round(net, 2))
                )
    return rows


def write_database(rows: list[Row], db_path: Path) -> None:
    """Replace the SQLite file at `db_path` with a fresh `sales` table holding `rows`."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute(CREATE_TABLE)
        connection.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)", rows)


def expected_answers(db_path: Path) -> dict[str, str | float]:
    """Run the expected-answer queries: the top region of 2025, then its Q2 2026 revenue."""
    with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as connection:
        region = connection.execute(EXPECTED_SQL["expected"]).fetchone()[0]
        gross = connection.execute(
            EXPECTED_SQL["expected_gross"], (region,)
        ).fetchone()[0]
        net = connection.execute(EXPECTED_SQL["expected_net"], (region,)).fetchone()[0]
    return {"expected": region, "expected_gross": gross, "expected_net": net}


def write_expected(questions_path: Path, answers: dict[str, str | float]) -> None:
    """Fill the `expected*` fields of the questions file with the computed answers."""
    questions = yaml.safe_load(questions_path.read_text())
    for question in questions:
        for key in question.keys() & answers.keys():
            question[key] = answers[key]
    header = (
        "# The expected values are written by data/seed.py from the seeded database.\n"
    )
    questions_path.write_text(
        header + yaml.safe_dump(questions, sort_keys=False, allow_unicode=True)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite file to write")
    parser.add_argument(
        "--questions", type=Path, default=QUESTIONS_PATH, help="questions.yaml to fill"
    )
    arguments = parser.parse_args()
    rows = build_rows()
    write_database(rows, arguments.db)
    write_expected(arguments.questions, expected_answers(arguments.db))
    print(
        f"wrote {len(rows)} rows to {arguments.db} and the expected answers to {arguments.questions}"
    )


if __name__ == "__main__":
    main()
