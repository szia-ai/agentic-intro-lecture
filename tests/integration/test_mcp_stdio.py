"""SI test: start the MCP server over stdio, as the notebooks do, and call both tools."""

import asyncio
import sys
from typing import Any

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

from agentic_demo.paths import SERVER_PATH


async def list_and_call_tools() -> tuple[list[str], str, dict[str, Any] | None]:
    parameters = StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)])
    async with (
        stdio_client(parameters) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        schema = await session.call_tool("get_schema")
        count = await session.call_tool(
            "run_sql", {"query": "SELECT COUNT(*) AS n FROM sales"}
        )
    assert isinstance(schema, CallToolResult) and isinstance(count, CallToolResult)
    first_block = schema.content[0]
    assert isinstance(first_block, TextContent)
    return (
        [tool.name for tool in tools.tools],
        first_block.text,
        count.structured_content,
    )


@pytest.mark.usefixtures("sales_db")
def test_server_over_stdio() -> None:
    names, schema, count = asyncio.run(list_and_call_tools())
    assert names == ["get_schema", "run_sql"]
    assert schema.startswith("CREATE TABLE sales")
    assert count == {"columns": ["n"], "rows": [[216]], "truncated": False}
