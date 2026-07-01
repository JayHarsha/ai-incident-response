"""
MCP client — speaks JSON-RPC 2.0 to the Java incident-service MCP server.

Uses the MCP Streamable HTTP transport:
  POST /mcp  →  single JSON-RPC request/response

The client does a lazy initialize handshake before the first tool call,
then reuses the same logical session for subsequent calls.
"""

import logging
import httpx

logger = logging.getLogger(__name__)


class McpClient:
    """Synchronous MCP client for the Java incident-service MCP server."""

    def __init__(self, java_service_url: str):
        self._url = f"{java_service_url}/mcp"
        self._request_id = 0
        self._initialized = False

    # ── Internal helpers ────────────────────────────────────────────────────

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _post(self, payload: dict) -> dict:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(self._url, json=payload)
            resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            err = data["error"]
            raise RuntimeError(f"MCP error {err['code']}: {err['message']}")
        return data.get("result", {})

    def _ensure_initialized(self) -> None:
        """Run the MCP initialize handshake once per client instance."""
        if self._initialized:
            return
        self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "incident-ai-service", "version": "1.0.0"},
            },
        })
        # Send initialized notification — fire and forget (no response expected)
        try:
            with httpx.Client(timeout=5.0) as client:
                client.post(
                    self._url,
                    json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                )
        except Exception:
            pass
        self._initialized = True
        logger.info("MCP session initialized → %s", self._url)

    # ── Public API ───────────────────────────────────────────────────────────

    def list_tools(self) -> list[dict]:
        """Discover available tools from the MCP server."""
        self._ensure_initialized()
        return self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {},
        }).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> str:
        """Invoke a named tool and return the text result."""
        self._ensure_initialized()
        result = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        content = result.get("content", [])
        text = content[0].get("text", "") if content else ""
        logger.debug("MCP tool '%s' returned: %s", name, text[:100])
        return text
