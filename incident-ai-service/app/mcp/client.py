"""
MCP client using the official mcp Python SDK.

Transport: Streamable HTTP  (POST /mcp — JSON-RPC 2.0)
Library:   mcp>=1.1.0       (pip install mcp)

The agent runs in daemon threads (no event loop), so asyncio.run() is safe
to use here as a sync wrapper around the async mcp SDK calls.
"""

import asyncio
import logging

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class McpClient:
    """Synchronous MCP client — wraps the async mcp SDK for use in LangGraph nodes."""

    def __init__(self, java_service_url: str):
        self._url = f"{java_service_url}/mcp"

    # ── Public sync API ──────────────────────────────────────────────────────

    def call_tool(self, name: str, arguments: dict) -> str:
        """Call an MCP tool and return the text result."""
        return asyncio.run(self._call_tool(name, arguments))

    def list_tools(self) -> list[dict]:
        """Discover available tools from the Java MCP server."""
        return asyncio.run(self._list_tools())

    # ── Async implementations (mcp SDK is fully async) ───────────────────────

    async def _call_tool(self, name: str, arguments: dict) -> str:
        async with streamablehttp_client(self._url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                text = result.content[0].text if result.content else ""
                logger.info("MCP tool '%s' → %s", name, text)
                return text

    async def _list_tools(self) -> list[dict]:
        async with streamablehttp_client(self._url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [{"name": t.name, "description": t.description} for t in result.tools]
