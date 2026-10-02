"""Unit tests for the MCP server's tool functions, called directly without a transport."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.server import MAX_ROWS, get_schema, run_sql

pytestmark = pytest.mark.usefixtures("sales_db")


def test_get_schema_returns_create_table() -> None:
    schema = get_schema()
    assert schema.startswith("CREATE TABLE sales")
    assert "net_revenue" in schema


def test_run_sql_runs_a_single_select() -> None:
    result = run_sql("  SELECT COUNT(*) AS n FROM sales;  ")
    assert result["columns"] == ["n"]
    assert result["rows"] == [[216]]
    assert result["truncated"] is False


def test_run_sql_caps_the_rows() -> None:
    result = run_sql("SELECT * FROM sales")
    assert len(result["rows"]) == MAX_ROWS
    assert result["truncated"] is True


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM sales WHERE month LIKE '2024%'",
        "INSERT INTO sales VALUES ('2026-10', 'EMEA', 'Pro', 1, 1.0, 1.0)",
        "SELECT 1; DROP TABLE sales",
        "PRAGMA table_info(sales)",
        "",
    ],
)
def test_run_sql_rejects_anything_but_one_select(query: str) -> None:
    with pytest.raises(ToolError, match="single SELECT"):
        run_sql(query)


def test_run_sql_reports_sql_errors_as_tool_errors() -> None:
    with pytest.raises(ToolError, match="SQL error"):
        run_sql("SELECT nope FROM sales")
