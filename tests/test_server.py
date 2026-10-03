"""Talk to server.py over real MCP (stdio), no API key needed."""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent


async def _call(name, args=None):
    server = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            out = await session.call_tool(name, args or {})
            return tools, json.loads(out.content[0].text)


def test_tools_listed_and_suburb_labelled():
    tools, data = asyncio.run(_call("get_suburb", {"name": "Newtown"}))
    assert tools == {"list_suburbs", "get_suburb", "find_suburbs_by_segment", "describe_columns"}
    s = data["suburb"]
    assert s["area_name"]["value"] == "Newtown (NSW)"
    assert s["median_rent_weekly"] == {"value": 550, "source": "census_2021"}
    assert s["est_population_2026"]["source"] == "modelled"


def test_unknown_suburb_says_not_available():
    _, data = asyncio.run(_call("get_suburb", {"name": "Brunswick"}))
    assert "not in this table" in data["error"]


def test_segment_lookup():
    _, data = asyncio.run(_call("find_suburbs_by_segment", {"segment": "mature affluent"}))
    assert data["suburbs"] == ["Mosman", "Vaucluse", "Castle Hill (NSW)"]
