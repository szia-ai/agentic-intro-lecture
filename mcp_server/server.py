"""Read-only MCP server over stdio with two tools: get_schema and run_sql."""

import sqlite3
from contextlib import closing
from typing import TypedDict

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from agentic_demo.paths import DB_PATH

MAX_ROWS = 50

server = MCPServer(
    "sales-db", instructions="Read-only access to the demo `sales` table."
)


# A TypedDict return becomes structured content; a bare dict does not.
class SqlResult(TypedDict):
    columns: list[str]
    rows: list[list[object]]
    truncated: bool


def connect() -> sqlite3.Connection:
    """Open the seeded database read-only."""
    if not DB_PATH.exists():
        raise ToolError("The database is missing: run `python data/seed.py` first.")
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


@server.tool()
def get_schema() -> str:
    """Return the CREATE TABLE statement of the `sales` table."""
    with closing(connect()) as connection:
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'sales'"
        ).fetchone()
    if row is None:
        raise ToolError(
            "The database has no `sales` table: run `python data/seed.py` first."
        )
    return row[0]


@server.tool()
def run_sql(query: str) -> SqlResult:
    """Run ONE read-only SELECT statement and return at most 50 rows."""
    # A first filter only: the read-only connection is the real guard. A `;` inside a string
    # literal is rejected too, which is fine for the demo. Only ToolError text reaches the model.
    statement = query.strip().rstrip(";").strip()
    if not statement.upper().startswith("SELECT") or ";" in statement:
        raise ToolError("Only a single SELECT statement is allowed.")
    try:
        with closing(connect()) as connection:
            cursor = connection.execute(statement)
            rows = cursor.fetchmany(MAX_ROWS + 1)
            columns = [description[0] for description in cursor.description]
    except sqlite3.Error as error:
        raise ToolError(f"SQL error: {error}") from error
    return SqlResult(
        columns=columns,
        rows=[list(row) for row in rows[:MAX_ROWS]],
        truncated=len(rows) > MAX_ROWS,
    )


if __name__ == "__main__":
    server.run(transport="stdio")
